# Next Session Activation Prompt

**Copy and paste this at the start of your next Claude Code session:**

---

We'll restart and continue development on the Vision System frontend. Last session we completed Book Builder Phase 1 & 2 (markdown editor with live preview) and Vision System backend (image upload with AI prompt detection, Claude OCR API integration).

Now we need to build:
1. ImageUploader component with folder recursion support
2. ImageGallery with grid/slideshow views
3. ImageBrowser modal for adding images to book sections

The backend is ready - we have upload endpoints with metadata extraction that detect DALL-E/Stable Diffusion/Midjourney prompts from EXIF data.

---

**What Claude Code will do:**

1. Run activation checklist (query ChromaDB for "session status report")
2. Review last session accomplishments
3. Enter PLAN MODE (present implementation plan for ImageUploader)
4. Get your approval before coding
5. Build frontend components with:
   - Folder selection (webkitdirectory attribute)
   - Drag-and-drop support
   - Upload progress tracking
   - Preview grid showing detected prompts/generators
   - Integration with vision/OCR workflow
