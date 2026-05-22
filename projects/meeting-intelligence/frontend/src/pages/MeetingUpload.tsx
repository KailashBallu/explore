import { useState } from "react";
import { useNavigate } from "react-router-dom";

type Step = "metadata" | "attendees" | "agenda" | "upload" | "confirm";

export default function MeetingUpload() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("metadata");

  const steps: { key: Step; label: string }[] = [
    { key: "metadata", label: "Meeting Details" },
    { key: "attendees", label: "Attendees" },
    { key: "agenda", label: "Agenda" },
    { key: "upload", label: "Upload Files" },
    { key: "confirm", label: "Confirm" },
  ];

  const currentIndex = steps.findIndex((s) => s.key === step);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-semibold text-gray-900">New Meeting</h1>
      </header>
      <main className="max-w-3xl mx-auto p-6">
        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-8">
          {steps.map((s, i) => (
            <div key={s.key} className="flex items-center gap-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  i <= currentIndex
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {i < currentIndex ? "✓" : i + 1}
              </div>
              <span
                className={`text-sm ${
                  i === currentIndex ? "text-blue-600 font-medium" : "text-gray-500"
                }`}
              >
                {s.label}
              </span>
              {i < steps.length - 1 && (
                <div className="w-8 h-px bg-gray-300 mx-1" />
              )}
            </div>
          ))}
        </div>

        {/* Step content - placeholder */}
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500">
          <p className="text-lg">Upload wizard step: {step}</p>
        </div>

        {/* Navigation */}
        <div className="flex justify-between mt-6">
          <button
            type="button"
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
            onClick={() => navigate("/")}
          >
            Cancel
          </button>
          <div className="flex gap-3">
            {currentIndex > 0 && (
              <button
                type="button"
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                onClick={() => setStep(steps[currentIndex - 1].key)}
              >
                Back
              </button>
            )}
            {currentIndex < steps.length - 1 ? (
              <button
                type="button"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                onClick={() => setStep(steps[currentIndex + 1].key)}
              >
                Next
              </button>
            ) : (
              <button
                type="button"
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                onClick={() => navigate("/")}
              >
                Start Generation
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
