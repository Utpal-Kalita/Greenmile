import Link from "next/link";
import { ArrowLeft, MapPinOff } from "lucide-react";

export default function NotFound() {
  return (
    <div className="error-state">
      <MapPinOff size={30} />
      <span className="eyebrow danger">404 / Off route</span>
      <h1>This stop isn’t on the loop.</h1>
      <div>
        <strong>What happened:</strong>
        <p>The page you requested does not exist in this Greenmile route.</p>
      </div>
      <Link className="primary-button" href="/">
        <ArrowLeft size={16} /> Return to trip
      </Link>
    </div>
  );
}
