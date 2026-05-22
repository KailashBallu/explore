import { useParams } from "react-router-dom";

export default function ReviewEditor() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-semibold text-gray-900">Review Minutes</h1>
      </header>
      <div className="flex flex-1">
        {/* Left: editable minutes */}
        <div className="flex-1 p-6 border-r border-gray-200 bg-white">
          <h2 className="text-lg font-medium text-gray-800 mb-4">Minutes</h2>
          <div className="text-gray-400 text-center py-12">
            Minutes editor coming soon (meeting {id})
          </div>
        </div>
        {/* Right: transcript / player */}
        <div className="w-[480px] p-6 bg-gray-50">
          <h2 className="text-lg font-medium text-gray-800 mb-4">Source</h2>
          <div className="text-gray-400 text-center py-12">
            Transcript view & audio player
          </div>
        </div>
      </div>
    </div>
  );
}
