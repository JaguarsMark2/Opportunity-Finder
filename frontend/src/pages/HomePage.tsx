/** Home/Landing page for Opportunity Finder. */

import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-900 dark:to-gray-800">
      {/* Hero section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
            Discover Your Next
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
              {' '}Big Opportunity
            </span>
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
            AI-powered opportunity discovery platform that scans Reddit, Indie Hackers,
            Product Hunt, Hacker News, and more to find validated business opportunities
            tailored to you.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register"
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-medium"
            >
              Get Started Free
            </Link>
            <Link
              to="/login"
              className="px-8 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-lg font-medium"
            >
              Sign In
            </Link>
          </div>
        </div>

        {/* Features section */}
        <div className="mt-20">
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
            Everything you need to find opportunities
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                AI-Powered Discovery
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Our AI scans multiple platforms to find opportunities based on market trends,
                user discussions, and emerging needs.
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Validated Opportunities
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Each opportunity is scored and validated based on market demand, competition
                level, and multiple data sources.
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Track Progress
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Save opportunities, add notes, and track your progress from research to
                building your next venture.
              </p>
            </div>
          </div>
        </div>

        {/* Sources section */}
        <div className="mt-20 text-center">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-8">
            We scan opportunities from
          </h2>
          <div className="flex flex-wrap justify-center gap-8 items-center opacity-60">
            <span className="text-2xl font-bold text-orange-500">Reddit</span>
            <span className="text-2xl font-bold text-blue-500">Indie Hackers</span>
            <span className="text-2xl font-bold text-red-500">Product Hunt</span>
            <span className="text-2xl font-bold text-orange-600">Hacker News</span>
            <span className="text-2xl font-bold text-green-500">Google Trends</span>
          </div>
        </div>

        {/* CTA section */}
        <div className="mt-20 text-center bg-white dark:bg-gray-800 rounded-lg shadow-lg p-12">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Ready to find your next opportunity?
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-8">
            Join thousands of entrepreneurs discovering opportunities every day.
          </p>
          <Link
            to="/register"
            className="inline-block px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg font-medium"
          >
            Start Free Trial
          </Link>
        </div>
      </div>
    </div>
  );
}
