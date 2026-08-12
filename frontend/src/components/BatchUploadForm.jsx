import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
import StatusBadge from "./StatusBadge";
import {
  formatFieldName,
  formatValue,
} from "../utils/formatter";

function BatchUploadForm() {
  const [images, setImages] = useState([]);
  const [csvFile, setCsvFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleImagesChange(event) {
    const selectedImages = Array.from(event.target.files);

    setImages(selectedImages);
    setResult(null);
    setError("");
  }

  function handleCsvChange(event) {
    setCsvFile(event.target.files[0] || null);
    setResult(null);
    setError("");
  }

  async function handleBatchSubmit(event) {
    event.preventDefault();

    if (images.length === 0) {
      setError("Please select at least one label image.");
      return;
    }

    if (!csvFile) {
      setError("Please select an application-data CSV file.");
      return;
    }

    const requestData = new FormData();

    for (const image of images) {
      requestData.append("images", image);
    }

    requestData.append("csv_file", csvFile);

    try {
      setLoading(true);
      setError("");
      setResult(null);

      const response = await fetch(`${API_URL}/verify-batch`, {
        method: "POST",
        body: requestData,
      });

      const responseData = await response.json();

      if (!response.ok) {
        throw new Error(responseData.detail || "Batch verification failed.");
      }

      setResult(responseData);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="batch-section">
      <div className="section-heading">
        <span className="step-number">4</span>

        <div>
          <h2>Batch verification</h2>
          <p>
            Upload multiple labels and a CSV containing their application data.
          </p>
        </div>
      </div>

      <form className="batch-form" onSubmit={handleBatchSubmit}>
        <label>
          Label images
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            multiple
            onChange={handleImagesChange}
            required
          />
        </label>

        {images.length > 0 && (
          <div className="selected-files">
            <strong>{images.length} image(s) selected</strong>

            <ul>
              {images.map((image) => (
                <li key={`${image.name}-${image.lastModified}`}>
                  {image.name}
                </li>
              ))}
            </ul>
          </div>
        )}

        <label>
          Application data CSV
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={handleCsvChange}
            required
          />
        </label>

        {csvFile && (
          <p className="selected-file">Selected CSV: {csvFile.name}</p>
        )}

        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? "Uploading batch…" : "Verify batch"}
        </button>
      </form>

      {result && (
        <div className="batch-summary">
          <h3>Batch verification completed</h3>

          <p>
            Total records: <strong>{result.total_records}</strong>
          </p>

          <p>
            Successfully processed: <strong>{result.processed}</strong>
          </p>

          <p>
            Could not process: <strong>{result.error_count}</strong>
          </p>

          <p>
            Passed: <strong>{result.status_counts.PASS}</strong>
          </p>

          <p>
            Failed: <strong>{result.status_counts.FAIL}</strong>
          </p>

          <p>
            Needs review: <strong>{result.status_counts.NEEDS_REVIEW}</strong>
          </p>

          {result.errors?.length > 0 && (
            <div className="batch-errors">
              <h4>Records that could not be processed</h4>

              <ul>
                {result.errors.map((item, index) => (
                  <li key={`${item.filename}-${index}`}>
                    <strong>{item.filename}:</strong> {item.error}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {result.results?.length > 0 && (
            <div className="batch-results-list">
              <h4>Processed labels</h4>

              {result.results.map((labelResult) => (
                <article
                  className="batch-result-card"
                  key={labelResult.filename}
                >
                  <div className="field-result-header">
                    <div>
                      <h3>{labelResult.filename}</h3>
                      <small>
                        {(labelResult.processing_time_ms / 1000).toFixed(2)}{" "}
                        seconds
                      </small>
                    </div>

                    <StatusBadge status={labelResult.overall_status} />
                  </div>

                  <details className="ocr-details">
                    <summary>View field results</summary>

                    <div className="result-list">
                      {labelResult.validation_results.map((fieldResult) => (
                        <div className="field-result" key={fieldResult.field}>
                          <div className="field-result-header">
                            <strong>
                              {formatFieldName(fieldResult.field)}
                            </strong>

                            <StatusBadge status={fieldResult.status} />
                          </div>

                          <p>Expected: {formatValue(fieldResult.expected)}</p>

                          <p>Detected: {formatValue(fieldResult.detected)}</p>

                          {fieldResult.reason && (
                            <p className="result-reason">
                              {fieldResult.reason}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </details>
                </article>
              ))}
            </div>
          )}

          <details className="ocr-details">
            <summary>Developer details</summary>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </details>
        </div>
      )}
    </section>
  );
}

export default BatchUploadForm;
