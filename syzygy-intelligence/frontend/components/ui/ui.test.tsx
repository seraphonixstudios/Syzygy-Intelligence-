import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

describe("Card", () => {
  it("renders children", () => {
    render(<Card><p>hello</p></Card>);
    expect(screen.getByText("hello")).toBeInTheDocument();
  });

  it("applies glass class when glass prop is true", () => {
    const { container } = render(<Card glass>content</Card>);
    expect(container.firstChild?.className).toContain("syzygy-card-glass");
  });

  it("applies default card class without glass", () => {
    const { container } = render(<Card>content</Card>);
    expect(container.firstChild?.className).toContain("syzygy-card");
  });

  it("accepts additional class names", () => {
    const { container } = render(<Card className="extra-class">content</Card>);
    expect(container.firstChild?.className).toContain("extra-class");
  });
});

describe("CardHeader", () => {
  it("renders children", () => {
    render(<CardHeader><h3>header</h3></CardHeader>);
    expect(screen.getByText("header")).toBeInTheDocument();
  });
});

describe("CardTitle", () => {
  it("renders text", () => {
    render(<CardTitle>Title</CardTitle>);
    expect(screen.getByText("Title")).toBeInTheDocument();
  });
});

describe("CardDescription", () => {
  it("renders text", () => {
    render(<CardDescription>Description</CardDescription>);
    expect(screen.getByText("Description")).toBeInTheDocument();
  });
});

describe("CardContent", () => {
  it("renders children", () => {
    render(<CardContent>content</CardContent>);
    expect(screen.getByText("content")).toBeInTheDocument();
  });
});

describe("CardFooter", () => {
  it("renders children", () => {
    render(<CardFooter>footer</CardFooter>);
    expect(screen.getByText("footer")).toBeInTheDocument();
  });
});

describe("Badge", () => {
  it("renders text", () => {
    render(<Badge>status</Badge>);
    expect(screen.getByText("status")).toBeInTheDocument();
  });

  it("applies variant classes", () => {
    const { container } = render(<Badge variant="masculine">gold</Badge>);
    expect(container.firstChild?.className).toContain("syzygy-gold");
  });

  it("applies unified variant", () => {
    const { container } = render(<Badge variant="unified">bone</Badge>);
    expect(container.firstChild?.className).toContain("syzygy-bone");
  });
});

describe("Button", () => {
  it("renders text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("applies gold variant classes", () => {
    const { container } = render(<Button variant="gold">Gold</Button>);
    expect(container.firstChild?.className).toContain("syzygy-gold");
  });

  it("applies size classes", () => {
    const { container } = render(<Button size="sm">Small</Button>);
    expect(container.firstChild?.className).toContain("h-9");
  });

  it("is disabled when disabled prop is set", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByText("Disabled")).toBeDisabled();
  });

  it("forwards click handler", async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<Button onClick={onClick}>Click</Button>);
    await user.click(screen.getByText("Click"));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
