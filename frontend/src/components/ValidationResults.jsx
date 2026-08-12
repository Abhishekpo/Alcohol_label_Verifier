import StatusBadge from "./StatusBadge";
import {
  formatFieldName,
  formatStatus,
  formatValue,
} from "../utils/formatter";

function ValidationResults({ result, loading }) {
  return (
    <section className="results-panel" aria-live="polite">
      <div className="section-heading">
        <span className="step-number">3</span>

        <div>
          <h2>Verification results</h2>
          <p>Review matches, failures, and uncertain fields.</p>
        </div>
      </div>

      {!result && !loading && (
        <div className="empty-results">
          <div className="empty-symbol">✓</div>
          <h3>No verification performed</h3>

          <p>
            Complete the application fields and upload a label to see the
            comparison results.
          </p>
        </div>
      )}

      {loading && (
        <div className="loading-state">
          <div className="spinner" />
          <h3>Analyzing label</h3>
          <p>Extracting and validating the label information.</p>
        </div>
      )}

      {result && (
        <div className="result-content">
          <div
            className={`overall-card ${result.overall_status.toLowerCase()}`}
          >
            <div>
              <span>Overall result</span>
              <strong>{formatStatus(result.overall_status)}</strong>
            </div>

            <p>
              Completed in {(result.processing_time_ms / 1000).toFixed(2)}s
            </p>
          </div>

          <div className="result-list">
            {result.validation_results.map((item) => (
              <article className="field-result" key={item.field}>
                <div className="field-result-header">
                  <h3>{formatFieldName(item.field)}</h3>
                  <StatusBadge status={item.status} />
                </div>

                <dl>
                  <div>
                    <dt>Expected</dt>
                    <dd>{formatValue(item.expected)}</dd>
                  </div>

                  <div>
                    <dt>Detected</dt>
                    <dd>{formatValue(item.detected)}</dd>
                  </div>

                  {item.similarity_score !== undefined && (
                    <div>
                      <dt>Confidence</dt>
                      <dd>
                        {Number(item.similarity_score).toFixed(1)}%
                      </dd>
                    </div>
                  )}
                </dl>

                {item.reason && (
                  <p className="result-reason">{item.reason}</p>
                )}
              </article>
            ))}
          </div>

          <details className="ocr-details">
            <summary>Developer details</summary>
            <pre>{result.extracted_text}</pre>
          </details>
        </div>
      )}
    </section>
  );
}

export default ValidationResults;