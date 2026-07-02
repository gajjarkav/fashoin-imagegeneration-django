# HelLFasioN - Clothing Analysis & Styling Platform

A Django-based web application that analyzes clothing images using AI and generates styled outfits recommendations based on user preferences and themes.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Setup](#api-setup)
- [Usage](#usage)
- [Admin Panel](#admin-panel)
- [UI/UX Improvements](#uiux-improvements)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

---

## ✨ Features

- **Clothing Image Analysis**: Upload images and get AI-powered analysis
- **Color Detection**: Identifies dominant colors in clothing
- **Category Recognition**: Automatically detects clothing category and type
- **Style Recommendations**: Generates outfit suggestions based on themes:
  - Casual
  - Office/Professional
  - Party
  - Date Night
  - College
  - Vacation
  - Winter
  - Summer
  - Traditional
- **AI-Powered Insights**: Uses Google Gemini API for intelligent analysis
- **Image Generation**: Create styled outfit variations using multiple providers
- **Admin Dashboard**: Manage content and track usage

---

## 🛠️ Tech Stack

- **Backend**: Django 5.2.7
- **Database**: SQLite3
- **Image Processing**: Pillow 11.3.0
- **AI Models**: 
  - Google Generative AI (Gemini)
  - Replicate (Stable Diffusion models)
- **Cloud Services**:
  - Cloudflare (Image processing)
  - ImageKit (Image optimization)
- **Environment Management**: python-dotenv
- **HTTP Requests**: Requests library

---

## 📦 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- API keys from:
  - Google Cloud (for Gemini API)
  - Replicate
  - ImageKit
  - Cloudflare (optional)

---


### Step 1: Install Dependencies

Direct installation (without virtual environment) (Quick Fast):

```bash
pip install -r requirements.txt
```

**OR** Using virtual environment :

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Initialize Database

```bash
python manage.py migrate
```

### Step 3: Create Superuser (for Admin Access)

```bash
python manage.py createsuperuser
```

You'll be prompted to enter:
- Username
- Email
- Password

### Step 4: Create Media Directories

```bash
mkdir -p media/uploads
mkdir -p media/generated
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Image Provider (options: replicate, cloudflare, imagekit)
IMAGE_PROVIDER=replicate

# Google Gemini API
GOOGLE_API_KEY=your-google-api-key

# Replicate API
REPLICATE_API_TOKEN=your-replicate-token

# ImageKit Configuration
IMAGEKIT_PUBLIC_KEY=your-imagekit-public-key
IMAGEKIT_PRIVATE_KEY=your-imagekit-private-key
IMAGEKIT_URL_ENDPOINT=your-imagekit-url-endpoint

# Cloudflare Configuration (Optional)
CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
```

### settings.py Configuration

The app automatically reads from `.env` file using `python-dotenv`. Key configurations:

```python
# config/settings.py
DEBUG = os.getenv("DEBUG", False)
IMAGE_PROVIDER = "replicate"  # Change based on your preference
ALLOWED_HOSTS = []  # Add your domain in production
```

---

## 🔑 API Setup Guide

### 1. Google Generative AI (Gemini API)

**Purpose**: Image and text analysis, style recommendations

**Steps to Setup**:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the "Generative Language API"
4. Go to "Credentials" → Create API Key
5. Copy the API key to your `.env` file:
   ```env
   GOOGLE_API_KEY=your-api-key-here
   ```

**Documentation**: [Google Generative AI](https://ai.google.dev/)

---

### 2. Replicate API

**Purpose**: Image generation using AI models (Stable Diffusion, etc.)

**Steps to Setup**:

1. Visit [Replicate](https://replicate.com/)
2. Sign up for a free account
3. Go to API tokens section in account settings
4. Copy your API token
5. Add to `.env`:
   ```env
   REPLICATE_API_TOKEN=your-token-here
   ```

**Pricing**: Free tier available with usage limits

**Documentation**: [Replicate API Docs](https://replicate.com/docs)

---

### 3. ImageKit (Image Optimization)

**Purpose**: Optimize and serve images efficiently

**Steps to Setup**:

1. Visit [ImageKit.io](https://imagekit.io/)
2. Sign up for free account
3. Go to Settings → Developer Options
4. Copy:
   - Public Key
   - Private Key
   - URL Endpoint
5. Add to `.env`:
   ```env
   IMAGEKIT_PUBLIC_KEY=your-public-key
   IMAGEKIT_PRIVATE_KEY=your-private-key
   IMAGEKIT_URL_ENDPOINT=your-url-endpoint
   ```

**Documentation**: [ImageKit Documentation](https://docs.imagekit.io/)

---

### 4. Cloudflare (Optional - Image Processing)

**Purpose**: Advanced image processing and CDN

**Steps to Setup**:

1. Visit [Cloudflare](https://www.cloudflare.com/)
2. Create account and add your domain
3. Go to Account Settings → API Tokens
4. Create token with appropriate permissions
5. Add to `.env`:
   ```env
   CLOUDFLARE_ACCOUNT_ID=your-account-id
   CLOUDFLARE_API_TOKEN=your-api-token
   ```

**Documentation**: [Cloudflare API](https://developers.cloudflare.com/)

---

## 📖 Usage

### Running the Development Server

```bash
# Activate virtual environment (if using one)
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Run server
python manage.py runserver

# Server will be available at http://127.0.0.1:8000/
```

### Using the Application

1. **Home Page**: Visit `http://127.0.0.1:8000/`
2. **Upload Image**: Navigate to upload section
3. **Select Theme**: Choose styling theme preference
4. **View Analysis**: Get AI-powered clothing analysis
5. **Generate Styles**: Create styled outfit recommendations

---

## 🔐 Admin Panel Setup

### Access Admin Panel

1. Start the development server
2. Visit: `http://127.0.0.1:8000/admin/`
3. Log in with superuser credentials created during installation

### Admin Features

- **Users Management**: Create, edit, delete user accounts
- **Upload Management**: View uploaded images and their status
- **Analysis Tracking**: Monitor AI analysis results
- **Style Sessions**: Track user style preferences and recommendations
- **Generated Images**: View and manage generated outfit images

### Creating Admin User from Command Line

```bash
python manage.py createsuperuser --username=admin --email=admin@example.com
```

---

## 🎨 UI/UX Improvements

### Current Areas for Enhancement

#### 1. **Home Page**
- [ ] Add hero section with project overview
- [ ] Include feature highlights/benefits
- [ ] Add social proof (testimonials, usage stats)
- [ ] Call-to-action buttons more prominent

#### 2. **Upload Section**
- [ ] Add drag-and-drop functionality
- [ ] Show upload progress bar
- [ ] Add image preview before upload
- [ ] Include file size validation UI feedback
- [ ] Add multiple file upload support

#### 3. **Analysis Display**
- [ ] Create interactive cards for clothing details
- [ ] Add visual color palette display
- [ ] Show confidence scores for AI predictions
- [ ] Better layout for clothing category display

#### 4. **Results Page**
- [ ] Improve generated image gallery layout
- [ ] Add image comparison sliders
- [ ] Implement lightbox/modal for full-screen view
- [ ] Add share/download buttons for results
- [ ] Show styling tips based on analysis

#### 5. **Navigation & Layout**
- [ ] Sticky/fixed navigation header
- [ ] Mobile-responsive design improvements
- [ ] Add breadcrumb navigation
- [ ] Implement proper footer with links

#### 6. **Forms & Inputs**
- [ ] Better form styling and validation messages
- [ ] Add placeholder images/examples
- [ ] Form progress indicator
- [ ] Real-time validation feedback

#### 7. **Dark Mode**
- [ ] Implement dark/light theme toggle
- [ ] Improve contrast and readability
- [ ] Themed images and backgrounds

#### 8. **Performance & Loading**
- [ ] Add skeleton loaders for images
- [ ] Implement image lazy loading
- [ ] Show loading states during processing
- [ ] Optimize CSS/JS loading

#### 9. **Accessibility**
- [ ] Add ARIA labels
- [ ] Improve keyboard navigation
- [ ] Better color contrast ratios
- [ ] Alt text for all images

#### 10. **Error Handling**
- [ ] User-friendly error messages
- [ ] Helpful error recovery suggestions
- [ ] Loading timeout indicators

### Recommended CSS/Design Framework

Consider integrating:
- **Tailwind CSS** or **Bootstrap 5** for responsive design
- **Swiper.js** for image carousels
- **Alpine.js** for interactive components
- **Animate.css** for smooth animations

---

## 🔧 Troubleshooting

### Issue: API Key Errors

**Solution**: 
- Verify `.env` file exists in project root
- Check API key format (no extra spaces)
- Ensure API is enabled in respective provider's console

### Issue: Image Upload Fails

**Solution**:
- Check media folder permissions: `chmod -R 755 media/`
- Verify PIL/Pillow is installed correctly
- Check file size limits in settings

### Issue: Database Errors

**Solution**:
```bash
# Delete existing database and migrations
rm db.sqlite3
python manage.py migrate
```

### Issue: Import Errors

**Solution**:
```bash
# Reinstall requirements
pip install --upgrade -r requirements.txt
```

### Issue: Port Already in Use

**Solution**:
```bash
# Use different port
python manage.py runserver 8001
```

---

## 📁 Project Structure

```
HelLFasioN/
├── config/                 # Django configuration
│   ├── settings.py        # Main settings
│   ├── urls.py           # URL routing
│   ├── wsgi.py           # WSGI configuration
│   └── asgi.py           # ASGI configuration
│
├── stylist/              # Main app
│   ├── models.py         # Database models
│   ├── views.py          # View handlers
│   ├── forms.py          # Django forms
│   ├── urls.py           # App URLs
│   ├── admin.py          # Admin configurations
│   ├── constants.py      # App constants
│   ├── utils.py          # Utility functions
│   │
│   ├── services/         # Business logic
│   │   ├── workflow.py   # Main workflow
│   │   ├── gemini.py     # Google Gemini integration
│   │   ├── replicate.py  # Replicate API integration
│   │   ├── cloudflare.py # Cloudflare integration
│   │   ├── imagekit.py   # ImageKit integration
│   │   ├── huggingface.py# HuggingFace integration
│   │   ├── image_utils.py# Image processing utilities
│   │   └── prompts.py    # AI prompts
│   │
│   ├── templates/        # HTML templates
│   │   └── stylist/
│   │       ├── home.html
│   │       ├── upload.html
│   │       ├── analysis.html
│   │       ├── results.html
│   │       └── error.html
│   │
│   ├── static/           # CSS, JS, images
│   │   └── stylist/
│   │       ├── css/
│   │       ├── js/
│   │       └── images/
│   │
│   └── migrations/       # Database migrations
│
├── templates/            # Base templates
│   └── base.html
│
├── media/               # User uploads & generated images
│   ├── uploads/
│   └── generated/
│
├── static/              # App static files
├── db.sqlite3          # SQLite database
├── manage.py           # Django management
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 📝 Requirements

```
Django==5.2.7
python-dotenv==1.1.1
Pillow==11.3.0
google-genai==1.38.0
requests==2.32.5
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📞 Support & Contact

For issues, questions, or suggestions:
- Create an issue in the repository
- Contact the development team
- Check existing documentation

---

## 🗺️ Roadmap

- [ ] User authentication & profiles
- [ ] Save favorite styles
- [ ] Style history tracking
- [ ] Advanced search filters
- [ ] Mobile app version
- [ ] Real-time collaborative styling
- [ ] Machine learning model for personalized recommendations
- [ ] Integration with fashion e-commerce
- [ ] Video tutorials
- [ ] API for third-party integrations

---

**Last Updated**: July 2026
**Version**: 1.0.0
