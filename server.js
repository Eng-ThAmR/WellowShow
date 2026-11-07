const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const ROOT = __dirname;
const DEFAULT_ADMIN_PASSWORD = 'ASDF@asdf1234';
const PASSWORD_FILE = path.join(ROOT, 'data', 'admin-password.txt');
const UPLOAD_DIR = path.join(ROOT, 'uploads');
const DB_FILE = path.join(ROOT, 'data', 'gallery.json');

function ensurePasswordStorage() {
  fs.mkdirSync(path.dirname(PASSWORD_FILE), { recursive: true });
  if (!fs.existsSync(PASSWORD_FILE)) {
    const initialPassword = process.env.ADMIN_PASSWORD || DEFAULT_ADMIN_PASSWORD;
    fs.writeFileSync(PASSWORD_FILE, initialPassword, 'utf8');
  }
}

function getStoredAdminPassword() {
  ensurePasswordStorage();
  const storedPassword = fs.readFileSync(PASSWORD_FILE, 'utf8').trim();
  if (storedPassword) return storedPassword;
  const fallbackPassword = process.env.ADMIN_PASSWORD || DEFAULT_ADMIN_PASSWORD;
  fs.writeFileSync(PASSWORD_FILE, fallbackPassword, 'utf8');
  return fallbackPassword;
}

let ADMIN_PASSWORD = getStoredAdminPassword();
function changeAdminPassword(nextPassword) {
  const cleanedPassword = String(nextPassword || '').trim();
  if (!cleanedPassword) throw new Error('A password is required.');
  ADMIN_PASSWORD = cleanedPassword;
  fs.writeFileSync(PASSWORD_FILE, cleanedPassword, 'utf8');
}

fs.mkdirSync(UPLOAD_DIR, { recursive: true });
fs.mkdirSync(path.dirname(DB_FILE), { recursive: true });
if (!fs.existsSync(DB_FILE)) fs.writeFileSync(DB_FILE, '[]');
let sessions = new Set();
const readGallery = () => JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
const writeGallery = data => fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, UPLOAD_DIR),
  filename: (_req, file, cb) => cb(null, crypto.randomUUID() + path.extname(file.originalname).toLowerCase())
});
const upload = multer({ storage, limits: { fileSize: 12 * 1024 * 1024, files: 20 }, fileFilter: (_req, file, cb) => cb(null, /^image\/(jpeg|png|webp|gif|avif)$/.test(file.mimetype)) });
function requireAdmin(req, res, next) {
  const token = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  if (!token || !sessions.has(token)) return res.status(401).json({ error: 'Admin login required' });
  next();
}
app.use(express.json());
app.use('/uploads', express.static(UPLOAD_DIR, { maxAge: '7d' }));
app.use(express.static(path.join(ROOT, 'public')));
app.post('/api/login', (req, res) => {
  if (String(req.body.password || '') !== ADMIN_PASSWORD) return res.status(401).json({ error: 'Invalid password' });
  const token = crypto.randomBytes(32).toString('hex'); sessions.add(token);
  res.json({ token });
});
app.put('/api/admin/password', requireAdmin, (req, res) => {
  const currentPassword = String(req.body.currentPassword || '').trim();
  const newPassword = String(req.body.newPassword || '').trim();

  if (!currentPassword || !newPassword) {
    return res.status(400).json({ error: 'Current and new passwords are required.' });
  }
  if (currentPassword !== ADMIN_PASSWORD) {
    return res.status(401).json({ error: 'Current password is incorrect.' });
  }
  if (newPassword.length < 8) {
    return res.status(400).json({ error: 'New password must be at least 8 characters long.' });
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
app.listen(PORT, () => console.log(`WellowNet portfolio running on http://localhost:${PORT}`));
