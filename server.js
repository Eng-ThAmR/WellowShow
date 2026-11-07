const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'admin123';
const ROOT = __dirname;
const UPLOAD_DIR = path.join(ROOT, 'uploads');
const DB_FILE = path.join(ROOT, 'data', 'gallery.json');
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
  if (req.body.password !== ADMIN_PASSWORD) return res.status(401).json({ error: 'Invalid password' });
  const token = crypto.randomBytes(32).toString('hex'); sessions.add(token);
  res.json({ token });
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
