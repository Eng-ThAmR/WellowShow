const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const ROOT = __dirname;
const PASSWORD_FILE = path.join(ROOT, 'data', 'admin-password.txt');
const UPLOAD_DIR = path.join(ROOT, 'uploads');
const DB_FILE = path.join(ROOT, 'data', 'gallery.json');
const IMAGE_EXTENSIONS = {
  'image/jpeg': '.jpg',
  'image/png': '.png',
  'image/webp': '.webp',
  'image/gif': '.gif',
  'image/avif': '.avif'
};

function configuredAdminPassword() {
  const password = process.env.ADMIN_PASSWORD || '';
  if (password.length < 12 || password !== password.trim()) {
    throw new Error('Set ADMIN_PASSWORD to at least 12 characters in the environment or .env before starting the server.');
  }
  return password;
}

function ensurePasswordStorage() {
  fs.mkdirSync(path.dirname(PASSWORD_FILE), { recursive: true });
  if (!fs.existsSync(PASSWORD_FILE)) {
    fs.writeFileSync(PASSWORD_FILE, configuredAdminPassword(), { encoding: 'utf8', mode: 0o600 });
  }
}

function getStoredAdminPassword() {
  ensurePasswordStorage();
  const storedPassword = fs.readFileSync(PASSWORD_FILE, 'utf8').trim();
  if (storedPassword) return storedPassword;
  const fallbackPassword = configuredAdminPassword();
  fs.writeFileSync(PASSWORD_FILE, fallbackPassword, { encoding: 'utf8', mode: 0o600 });
  return fallbackPassword;
}

let ADMIN_PASSWORD = getStoredAdminPassword();
function changeAdminPassword(nextPassword) {
  const cleanedPassword = String(nextPassword || '').trim();
  if (cleanedPassword.length < 12) throw new Error('Password must be at least 12 characters long.');
  fs.writeFileSync(PASSWORD_FILE, cleanedPassword, { encoding: 'utf8', mode: 0o600 });
  ADMIN_PASSWORD = cleanedPassword;
}

fs.mkdirSync(UPLOAD_DIR, { recursive: true });
fs.mkdirSync(path.dirname(DB_FILE), { recursive: true });
if (!fs.existsSync(DB_FILE)) fs.writeFileSync(DB_FILE, '[]');
let sessions = new Set();
const readGallery = () => JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
const writeGallery = data => fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, UPLOAD_DIR),
  filename: (_req, file, cb) => cb(null, crypto.randomUUID() + IMAGE_EXTENSIONS[file.mimetype])
});
const upload = multer({
  storage,
  limits: { fileSize: 12 * 1024 * 1024, files: 20 },
  fileFilter: (_req, file, cb) => cb(null, Object.hasOwn(IMAGE_EXTENSIONS, file.mimetype))
});
function requireAdmin(req, res, next) {
  const token = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  if (!token || !sessions.has(token)) return res.status(401).json({ error: 'Admin login required' });
  next();
}
app.disable('x-powered-by');
app.use((_req, res, next) => {
  res.set({
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
  });
  next();
});
app.use(express.json({ limit: '32kb' }));
app.use('/uploads', express.static(UPLOAD_DIR, { maxAge: '7d', immutable: true }));
app.use(express.static(path.join(ROOT, 'public')));
app.post('/api/login', (req, res) => {
  if (String((req.body && req.body.password) || '') !== ADMIN_PASSWORD) return res.status(401).json({ error: 'Invalid password' });
  const token = crypto.randomBytes(32).toString('hex'); sessions.add(token);
  res.json({ token });
});
app.put('/api/admin/password', requireAdmin, (req, res) => {
  const currentPassword = String((req.body && req.body.currentPassword) || '').trim();
  const newPassword = String((req.body && req.body.newPassword) || '').trim();

  if (!currentPassword || !newPassword) {
    return res.status(400).json({ error: 'Current and new passwords are required.' });
  }
  if (currentPassword !== ADMIN_PASSWORD) {
    return res.status(401).json({ error: 'Current password is incorrect.' });
  }
  if (newPassword.length < 12) {
    return res.status(400).json({ error: 'New password must be at least 12 characters long.' });
  }
  if (newPassword === currentPassword) {
    return res.status(400).json({ error: 'Choose a new password that is different from the current one.' });
  }

  changeAdminPassword(newPassword);
  sessions.clear();
  return res.json({ ok: true, message: 'Password updated. Please sign in again.' });
});
app.get('/api/gallery', (_req, res) => res.json(readGallery()));
app.post('/api/gallery', requireAdmin, upload.array('images', 20), (req, res) => {
  const gallery = readGallery();
  const added = (req.files || []).map(file => ({ id: crypto.randomUUID(), name: path.basename(file.originalname), url: '/uploads/' + file.filename }));
  writeGallery([...gallery, ...added]); res.status(201).json(added);
});
app.delete('/api/gallery/:id', requireAdmin, (req, res) => {
  const gallery = readGallery(); const item = gallery.find(x => x.id === req.params.id);
  if (!item) return res.status(404).json({ error: 'Image not found' });
  const filename = path.basename(item.url); const filePath = path.join(UPLOAD_DIR, filename);
  if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
  writeGallery(gallery.filter(x => x.id !== item.id)); res.json({ ok: true });
});
app.get('/health', (_req, res) => res.json({ ok: true }));
app.use('/api', (_req, res) => res.status(404).json({ error: 'API route not found' }));
app.use((error, req, res, next) => {
  if (res.headersSent) return next(error);
  const status = error instanceof multer.MulterError ? 400 : (error.status || 500);
  if (status >= 500) console.error(error);
  const message = status >= 500 ? 'Internal server error' : error.message;
  if (req.path.startsWith('/api/')) return res.status(status).json({ error: message });
  return res.status(status).send(message);
});
app.listen(PORT, () => console.log(`WellowNet portfolio running on http://localhost:${PORT}`));
