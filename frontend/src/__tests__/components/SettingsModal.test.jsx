import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WorkspaceProvider } from '../../contexts/WorkspaceContext';
import SettingsModal from '../../components/SettingsModal';

describe('SettingsModal', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  const renderModal = (isOpen = true) => {
    return render(
      <WorkspaceProvider>
        <SettingsModal isOpen={isOpen} onClose={mockOnClose} />
      </WorkspaceProvider>
    );
  };

  it('should not render when isOpen is false', () => {
    renderModal(false);
    expect(screen.queryByText('Settings')).not.toBeInTheDocument();
  });

  it('should render when isOpen is true', () => {
    renderModal(true);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('should display all setting sections', () => {
    renderModal();

    expect(screen.getByText('Display Settings')).toBeInTheDocument();
    expect(screen.getByText('Content Filtering')).toBeInTheDocument();
    expect(screen.getByText('Appearance')).toBeInTheDocument();
    expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
  });

  it('should show items per page dropdown', () => {
    renderModal();

    // Find by text content since labels may not be properly associated
    expect(screen.getByText(/Items Per Page/i)).toBeInTheDocument();

    const selects = document.querySelectorAll('select');
    const itemsSelect = Array.from(selects).find(s =>
      s.closest('div').textContent.includes('Items Per Page')
    );

    expect(itemsSelect).toBeTruthy();
    expect(itemsSelect.value).toBe('100');
  });

  it('should allow changing items per page', () => {
    renderModal();

    const selects = document.querySelectorAll('select');
    const itemsSelect = Array.from(selects).find(s =>
      s.closest('div').textContent.includes('Items Per Page')
    );

    fireEvent.change(itemsSelect, { target: { value: '200' } });

    expect(itemsSelect.value).toBe('200');
  });

  it('should show default API limit input', () => {
    renderModal();

    expect(screen.getByText(/Default API Limit/i)).toBeInTheDocument();

    const inputs = document.querySelectorAll('input[type="number"]');
    const limitInput = Array.from(inputs).find(i =>
      i.closest('div').textContent.includes('Default API Limit')
    );

    expect(limitInput).toBeTruthy();
    expect(limitInput.value).toBe('100');
  });

  it('should allow changing default API limit', () => {
    renderModal();

    const inputs = document.querySelectorAll('input[type="number"]');
    const limitInput = Array.from(inputs).find(i =>
      i.closest('div').textContent.includes('Default API Limit')
    );

    fireEvent.change(limitInput, { target: { value: '150' } });

    expect(limitInput.value).toBe('150');
  });

  it('should show system messages toggle', () => {
    renderModal();

    expect(screen.getByText('Show System Messages')).toBeInTheDocument();
  });

  it('should toggle system messages', () => {
    renderModal();

    const toggle = screen.getByRole('checkbox');
    expect(toggle).not.toBeChecked();

    fireEvent.click(toggle);
    expect(toggle).toBeChecked();
  });

  it('should show theme selector', () => {
    renderModal();

    expect(screen.getByText(/Theme/i)).toBeInTheDocument();

    const selects = document.querySelectorAll('select');
    const themeSelect = Array.from(selects).find(s =>
      s.closest('div').textContent.includes('Theme')
    );

    expect(themeSelect).toBeTruthy();
    expect(themeSelect.value).toBe('dark');
  });

  it('should display keyboard shortcuts reference', () => {
    renderModal();

    expect(screen.getByText('Focus Search')).toBeInTheDocument();
    expect(screen.getByText('Navigate Messages')).toBeInTheDocument();
    expect(screen.getByText('Close Modal/Clear')).toBeInTheDocument();
    expect(screen.getByText('Save')).toBeInTheDocument();
  });

  it('should call onClose when Cancel is clicked', () => {
    renderModal();

    fireEvent.click(screen.getByText('Cancel'));
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should call onClose when X button is clicked', () => {
    renderModal();

    const closeButton = screen.getByTitle('Close');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should save changes and close when Save Changes is clicked', () => {
    renderModal();

    // Change a setting
    const selects = document.querySelectorAll('select');
    const itemsSelect = Array.from(selects).find(s =>
      s.closest('div').textContent.includes('Items Per Page')
    );
    fireEvent.change(itemsSelect, { target: { value: '500' } });

    // Click save
    fireEvent.click(screen.getByText('Save Changes'));

    expect(mockOnClose).toHaveBeenCalled();

    // Settings should be persisted to localStorage
    const saved = localStorage.getItem('humanizer-preferences');
    expect(saved).toBeTruthy();
    const preferences = JSON.parse(saved);
    expect(preferences.itemsPerPage).toBe(500);
  });

  it('should reset to defaults when Reset button is clicked', () => {
    renderModal();

    // Change settings
    const selects = document.querySelectorAll('select');
    const itemsSelect = Array.from(selects).find(s =>
      s.closest('div').textContent.includes('Items Per Page')
    );

    const inputs = document.querySelectorAll('input[type="number"]');
    const limitInput = Array.from(inputs).find(i =>
      i.closest('div').textContent.includes('Default API Limit')
    );

    fireEvent.change(itemsSelect, { target: { value: '2000' } });
    fireEvent.change(limitInput, { target: { value: '500' } });

    // Reset
    fireEvent.click(screen.getByText('Reset to Defaults'));

    // Should be back to defaults
    expect(itemsSelect.value).toBe('100');
    expect(limitInput.value).toBe('100');
  });

  it('should call onClose when clicking outside modal', () => {
    renderModal();

    const backdrop = document.querySelector('.fixed.inset-0.bg-black');
    fireEvent.click(backdrop);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should NOT close when clicking inside modal', () => {
    renderModal();

    const modalContent = screen.getByText('Settings').closest('.bg-gray-900');
    fireEvent.click(modalContent);

    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('should load initial preferences from context', () => {
    // Set initial preferences
    localStorage.setItem('humanizer-preferences', JSON.stringify({
      itemsPerPage: 200,
      defaultLimit: 150,
      showSystemMessages: true,
      theme: 'dark'
    }));

    renderModal();

    const selects = document.querySelectorAll('select');
    const itemsSelect = Array.from(selects).find(s =>
      s.closest('div').textContent.includes('Items Per Page')
    );

    const inputs = document.querySelectorAll('input[type="number"]');
    const limitInput = Array.from(inputs).find(i =>
      i.closest('div').textContent.includes('Default API Limit')
    );

    const toggle = screen.getByRole('checkbox');

    expect(itemsSelect.value).toBe('200');
    expect(limitInput.value).toBe('150');
    expect(toggle).toBeChecked();
  });

  it('should reset unsaved changes when reopening', () => {
    renderModal();

    // Change a setting but don't save
    const selects = document.querySelectorAll('select');
    const itemsSelect = Array.from(selects).find(s =>
      s.closest('div').textContent.includes('Items Per Page')
    );
    fireEvent.change(itemsSelect, { target: { value: '500' } });

    // Value changed
    expect(itemsSelect.value).toBe('500');

    // Close modal (without saving - click Cancel)
    fireEvent.click(screen.getByText('Cancel'));

    expect(mockOnClose).toHaveBeenCalled();

    // Verify preferences weren't saved
    const saved = localStorage.getItem('humanizer-preferences');
    const preferences = saved ? JSON.parse(saved) : { itemsPerPage: 100 };
    expect(preferences.itemsPerPage).toBe(100); // Still default
  });
});
