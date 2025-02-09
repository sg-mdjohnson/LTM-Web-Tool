import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import MainLayout from '../MainLayout';
import { AuthProvider } from '../../../contexts/AuthContext';

describe('MainLayout', () => {
  it('renders correctly', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <MainLayout>
            <div>Test Content</div>
          </MainLayout>
        </AuthProvider>
      </BrowserRouter>
    );
    
    expect(screen.getByText('LTM Web Tool')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });
}); 