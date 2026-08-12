import { useEffect, useState } from "react";
import "./App.css";
import ValidationResults from "./components/ValidationResults";
import BatchUploadForm from "./components/BatchUploadForm";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const initialForm = {
  brandName: "",
  classType: "",
  alcoholPercentage: "",
  netContentsAmount: "",
  netContentsUnit: "ml",
};
function App() {
  const [form, setForm] = useState(initialForm);
  const [image, setImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (!image) {
      setPreviewUrl("");
      return;
    }

    const url = URL.createObjectURL(image);
    setPreviewUrl(url);

    return () => URL.revokeObjectURL(url);
  }, [image]);

  function handleInputChange(event) {
    const { name, value } = event.target;

    setForm((previousForm) => ({
      ...previousForm,
      [name]: value,
    }));
  }

  function handleImageChange(event) {
    const selectedImage = event.target.files[0];

    setImage(selectedImage || null);
    setResult(null);
    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!image) {
      setError("Please select a label image.");
      return;
    }

    const formData = new FormData();

    formData.append("image", image);
    formData.append("brand_name", form.brandName);
    formData.append("class_type", form.classType);
    formData.append("alcohol_percentage", form.alcoholPercentage);

    formData.append(
      "net_contents",
      `${form.netContentsAmount} ${form.netContentsUnit}`
    );

    try {
      setLoading(true);
      setError("");
      setResult(null);

      const response = await fetch(`${API_URL}/verify`, {
        method: "POST",
        body: formData,
      });

      const responseData = await response.json();

      if (!response.ok) {
        throw new Error(
          responseData.detail || "The label could not be verified."
        );
      }

      setResult(responseData);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  function resetForm() {
    setForm(initialForm);
    setImage(null);
    setResult(null);
    setError("");
  }

  return (
    <main className="app">
      <header className="page-header">
        <div>
          <p className="eyebrow">TTB compliance assistance</p>
          <h1>Alcohol Label Verifier</h1>
          <p className="subtitle">
            Compare label artwork with COLA application data and identify fields
            requiring human review.
          </p>
        </div>
      </header>

      <section className="workspace">
        <form className="verification-form" onSubmit={handleSubmit}>
          <div className="section-heading">
            <span className="step-number">1</span>
            <div>
              <h2>Application information</h2>
              <p>Enter the values submitted in the COLA application.</p>
            </div>
          </div>

          <label>
            Brand name
            <input
              type="text"
              name="brandName"
              value={form.brandName}
              onChange={handleInputChange}
              placeholder="OLD TOM DISTILLERY"
              required
            />
          </label>

          <label>
            Class or type
            <input
              type="text"
              name="classType"
              value={form.classType}
              onChange={handleInputChange}
              placeholder="Kentucky Straight Bourbon Whiskey"
              required
            />
          </label>

          <div className="field-row">
            <label>
              Alcohol percentage %
              <input
                type="number"
                name="alcoholPercentage"
                value={form.alcoholPercentage}
                onChange={handleInputChange}
                placeholder="45"
                min="0"
                max="100"
                step="0.01"
                required
              />
            </label>

            <label>
              Net contents (ml, L, or fl oz)
              <div className="net-contents-control">
                <input
                  type="number"
                  name="netContentsAmount"
                  value={form.netContentsAmount}
                  onChange={handleInputChange}
                  placeholder="750"
                  min="0.01"
                  step="0.01"
                  required
                />

                <select
                  name="netContentsUnit"
                  value={form.netContentsUnit}
                  onChange={handleInputChange}
                  aria-label="Net contents unit"
                >
                  <option value="ml">mL</option>
                  <option value="l">L</option>
                  <option value="floz">fl oz</option>
                </select>
              </div>
            </label>
          </div>

          <div className="section-heading upload-heading">
            <span className="step-number">2</span>
            <div>
              <h2>Label artwork</h2>
              <p>Upload a clear PNG, JPEG, or WebP image.</p>
            </div>
          </div>

          <label className="upload-area">
            <input
              className="file-input"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={handleImageChange}
            />

            {previewUrl ? (
              <img
                className="image-preview"
                src={previewUrl}
                alt="Selected alcohol label preview"
              />
            ) : (
              <div className="upload-placeholder">
                <span className="upload-icon">↑</span>
                <strong>Select a label image</strong>
                <span>PNG, JPEG or WebP · Maximum 10 MB</span>
              </div>
            )}
          </label>

          {image && <p className="selected-file">Selected: {image.name}</p>}

          {error && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}

          <div className="form-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={resetForm}
              disabled={loading}
            >
              Clear
            </button>

            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? "Verifying label…" : "Verify label"}
            </button>
          </div>
          
        </form>

          <ValidationResults
          result={result}
          loading={loading}
          />
         
      </section>
      <BatchUploadForm />
      
      <footer>
        This prototype supports human review and does not issue final COLA
        approval decisions.
      </footer>
    </main>
  );
}


export default App;
