import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// @testing-library/react auto-cleanup requires afterEach to be globally
// available. Since vitest does not expose globals by default, we register it
// explicitly here.
afterEach(() => {
  cleanup();
});
