# WellowNet Portfolio — Full Stack

## Features
- Responsive glassmorphism portfolio.
- Top admin toolbar with password login and image upload.
- Multi-image upload (up to 20 at a time; 12 MB each).
- Server-side image storage; gallery is visible to all visitors.
- Admin-only image deletion.

## Run locally
1. Install Node.js 18 or newer.
2. Optional: copy `.env.example` to `.env`. The default admin password is `admin123`.
3. Run `npm install`.
4. Run `npm start`.
5. Open `http://localhost:3000`.
6. On the site (not by opening `public/index.html` directly), go to **My Work Gallery** and select **Admin login**.
7. Enter the admin password, choose **Upload photos**, and select up to 20 JPEG, PNG, WebP, GIF, or AVIF images (maximum 12 MB each). Uploaded photos are saved on the server and shown to every visitor.

Set a private `ADMIN_PASSWORD` in `.env` before deployment. The built-in `admin123` password is for local development only and should not be used on a public site.

## Deployment
Deploy on a VPS or hosting service with persistent disk storage. The `uploads/` and `data/` folders must persist across restarts/deployments. This simple disk-storage version is not suitable for serverless platforms or ephemeral filesystems such as a default Vercel deployment. For Vercel, replace local upload storage with S3, Cloudinary, or Supabase Storage and use a database for gallery metadata.

Default admin password: `admin123`. Change it before exposing the site publicly by setting a strong `ADMIN_PASSWORD` in `.env` or your hosting environment. Use HTTPS in production; never commit `.env`.
