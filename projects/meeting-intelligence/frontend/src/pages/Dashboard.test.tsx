import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "./Dashboard";

describe("Dashboard", () => {
  it("renders the page title and empty state", () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    expect(screen.getByText("Meeting Intelligence")).toBeInTheDocument();
    expect(screen.getByText("No meetings yet")).toBeInTheDocument();
    expect(
      screen.getByText("Create your first meeting to generate minutes.")
    ).toBeInTheDocument();
  });

  it("has a link to create a new meeting", () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const links = screen.getAllByRole("link", { name: "New Meeting" });
    expect(links.length).toBeGreaterThan(0);
    expect(links[0]).toHaveAttribute("href", "/meetings/new");
  });
});
