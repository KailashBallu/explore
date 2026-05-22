import { Link } from "react-router-dom";

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-semibold text-gray-900">Meeting Intelligence</h1>
      </header>
      <main className="max-w-5xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-medium text-gray-800">Meetings</h2>
          <Link
            to="/meetings/new"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            New Meeting
          </Link>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center text-gray-500">
          <p className="text-lg mb-2">No meetings yet</p>
          <p className="text-sm">Create your first meeting to generate minutes.</p>
        </div>
      </main>
    </div>
  );
}
