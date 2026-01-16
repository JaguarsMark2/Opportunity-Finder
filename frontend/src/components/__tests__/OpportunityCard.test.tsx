import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import OpportunityCard from '../OpportunityCard';

describe('OpportunityCard', () => {
  const mockOpportunity = {
    id: '1',
    title: 'Test Opportunity',
    description: 'A test opportunity description',
    score: 75,
    is_validated: true,
    source_types: ['reddit', 'hacker_news'],
    created_at: '2024-01-15T00:00:00Z',
    mention_count: 5,
    competitor_count: 0,
    sources: [
      {
        id: '1',
        source_type: 'reddit',
        url: 'https://reddit.com/example',
        title: 'Test Source',
        engagement_metrics: { upvotes: 100, comments: 25 },
        collected_at: '2024-01-15T00:00:00Z'
      }
    ]
  };

  it('renders without crashing', () => {
    render(<OpportunityCard opportunity={mockOpportunity} onClick={() => {}} />);
  });

  it('renders opportunity title', () => {
    render(<OpportunityCard opportunity={mockOpportunity} onClick={() => {}} />);
    expect(screen.getByText('Test Opportunity')).toBeInTheDocument();
  });

  it('renders opportunity score', () => {
    render(<OpportunityCard opportunity={mockOpportunity} onClick={() => {}} />);
    expect(screen.getByText('75')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<OpportunityCard opportunity={mockOpportunity} onClick={handleClick} />);
    const card = screen.getByText('Test Opportunity').closest('div');
    if (card) {
      fireEvent.click(card);
      expect(handleClick).toHaveBeenCalledTimes(1);
    }
  });
});
