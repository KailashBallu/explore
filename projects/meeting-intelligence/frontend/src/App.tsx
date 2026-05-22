import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Dashboard from "./pages/Dashboard";
import MeetingUpload from "./pages/MeetingUpload";
import ReviewEditor from "./pages/ReviewEditor";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/meetings/new" element={<MeetingUpload />} />
          <Route path="/meetings/:id/review" element={<ReviewEditor />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
