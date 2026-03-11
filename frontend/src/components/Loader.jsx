export default function Loader({ visible, text }) {
  if (!visible) return null;

  return (
    <div className="loader">
      <div className="spinner"></div>
      <p>{text || 'Processing...'}</p>
    </div>
  );
}
