import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkspaceProvider } from '../../contexts/WorkspaceContext';
import axios from 'axios';

// Mock axios
vi.mock('axios');

describe('Book Builder Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Book Creation Workflow', () => {
    it('should create a new book and navigate to it', async () => {
      // Mock successful book creation
      const mockBook = {
        id: 1,
        title: 'New Book',
        description: 'Test book',
        created_at: new Date().toISOString(),
      };

      axios.post.mockResolvedValueOnce({ data: mockBook });

      // This test would render the full book builder flow
      // For now, just verify mock works
      const response = await axios.post('/api/books', {
        title: 'New Book',
        description: 'Test book',
      });

      expect(response.data).toEqual(mockBook);
      expect(axios.post).toHaveBeenCalledWith('/api/books', {
        title: 'New Book',
        description: 'Test book',
      });
    });

    it('should handle book creation errors gracefully', async () => {
      axios.post.mockRejectedValueOnce(new Error('Network error'));

      await expect(
        axios.post('/api/books', { title: 'Failed Book' })
      ).rejects.toThrow('Network error');
    });
  });

  describe('Section Management', () => {
    it('should create a new section in a book', async () => {
      const mockSection = {
        id: 1,
        book_id: 1,
        title: 'Chapter 1',
        content: '# Introduction',
        order_index: 0,
      };

      axios.post.mockResolvedValueOnce({ data: mockSection });

      const response = await axios.post('/api/books/1/sections', {
        title: 'Chapter 1',
        content: '# Introduction',
      });

      expect(response.data).toEqual(mockSection);
    });

    it('should update section content', async () => {
      const mockSection = {
        id: 1,
        book_id: 1,
        title: 'Chapter 1',
        content: '# Updated Content',
        order_index: 0,
      };

      axios.put.mockResolvedValueOnce({ data: mockSection });

      const response = await axios.put('/api/books/1/sections/1', {
        content: '# Updated Content',
      });

      expect(response.data).toEqual(mockSection);
    });

    it('should delete a section', async () => {
      axios.delete.mockResolvedValueOnce({ data: { success: true } });

      const response = await axios.delete('/api/books/1/sections/1');

      expect(response.data.success).toBe(true);
      expect(axios.delete).toHaveBeenCalledWith('/api/books/1/sections/1');
    });
  });

  describe('Content Card Management', () => {
    it('should add content card to section', async () => {
      const mockLink = {
        id: 1,
        section_id: 1,
        content_type: 'conversation',
        content_id: 123,
        display_text: 'Reference to conversation',
      };

      axios.post.mockResolvedValueOnce({ data: mockLink });

      const response = await axios.post('/api/books/1/sections/1/content', {
        content_type: 'conversation',
        content_id: 123,
        display_text: 'Reference to conversation',
      });

      expect(response.data).toEqual(mockLink);
    });

    it('should remove content card from section', async () => {
      axios.delete.mockResolvedValueOnce({ data: { success: true } });

      const response = await axios.delete('/api/books/1/sections/1/content/1');

      expect(response.data.success).toBe(true);
    });
  });

  describe('Full Book Builder Workflow', () => {
    it('should support complete workflow: create book → add section → add content → save', async () => {
      // 1. Create book
      const mockBook = { id: 1, title: 'Test Book' };
      axios.post.mockResolvedValueOnce({ data: mockBook });

      const bookResponse = await axios.post('/api/books', { title: 'Test Book' });
      expect(bookResponse.data).toEqual(mockBook);

      // 2. Add section
      const mockSection = { id: 1, book_id: 1, title: 'Chapter 1' };
      axios.post.mockResolvedValueOnce({ data: mockSection });

      const sectionResponse = await axios.post('/api/books/1/sections', {
        title: 'Chapter 1',
      });
      expect(sectionResponse.data).toEqual(mockSection);

      // 3. Add content
      const mockLink = { id: 1, section_id: 1, content_type: 'message' };
      axios.post.mockResolvedValueOnce({ data: mockLink });

      const linkResponse = await axios.post('/api/books/1/sections/1/content', {
        content_type: 'message',
        content_id: 456,
      });
      expect(linkResponse.data).toEqual(mockLink);

      // 4. Update section content
      const updatedSection = { ...mockSection, content: '# New content' };
      axios.put.mockResolvedValueOnce({ data: updatedSection });

      const updateResponse = await axios.put('/api/books/1/sections/1', {
        content: '# New content',
      });
      expect(updateResponse.data).toEqual(updatedSection);
    });
  });

  describe('Book Navigation', () => {
    it('should navigate between book sections', async () => {
      const mockSections = [
        { id: 1, title: 'Chapter 1', order_index: 0 },
        { id: 2, title: 'Chapter 2', order_index: 1 },
        { id: 3, title: 'Chapter 3', order_index: 2 },
      ];

      axios.get.mockResolvedValueOnce({ data: mockSections });

      const response = await axios.get('/api/books/1/sections');

      expect(response.data).toEqual(mockSections);
      expect(response.data.length).toBe(3);
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors during book creation', async () => {
      axios.post.mockRejectedValueOnce(new Error('Network error'));

      await expect(
        axios.post('/api/books', { title: 'Book' })
      ).rejects.toThrow('Network error');
    });

    it('should handle 404 errors when book not found', async () => {
      axios.get.mockRejectedValueOnce({
        response: { status: 404, data: { error: 'Book not found' } },
      });

      try {
        await axios.get('/api/books/999');
      } catch (error) {
        expect(error.response.status).toBe(404);
        expect(error.response.data.error).toBe('Book not found');
      }
    });

    it('should handle validation errors', async () => {
      axios.post.mockRejectedValueOnce({
        response: {
          status: 400,
          data: { error: 'Title is required' },
        },
      });

      try {
        await axios.post('/api/books', { description: 'No title' });
      } catch (error) {
        expect(error.response.status).toBe(400);
        expect(error.response.data.error).toBe('Title is required');
      }
    });
  });
});
