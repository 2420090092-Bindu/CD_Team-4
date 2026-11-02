
import { useState } from "react";
import "./ParseViz.css";

const API = "http://127.0.0.1:5000";

const DEFAULT_GRAMMAR = `E->TE'
E'->+TE'|epsilon
T->FT'
T'->*FT'|epsilon
F->(E)|id`;


// =====================================================
// API HELPER
// =====================================================

async function callAPI(endpoint, body) {

  const response = await fetch(`${API}${endpoint}`, {
    method: "POST",

    headers: {
      "Content-Type": "application/json"
    },

    body: JSON.stringify(body)
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "API request failed");
  }

  return data;
}


// =====================================================
// FORMAT PARSING TABLE PRODUCTION VALUES
// =====================================================

function formatProductionCell(value) {

  if (value === null || value === undefined) {
    return "ERROR";
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return "ERROR";
    }

    return value.map(formatProductionCell).join(" / ");
  }

  if (typeof value === "object") {

    // Direct production or text fields
    if (value.production !== undefined) {
      return formatProductionCell(value.production);
    }

    if (value.text !== undefined) {
      return String(value.text);
    }

    if (value.rule !== undefined) {
      return formatProductionCell(value.rule);
    }

    // Production represented using LHS and RHS
    const lhs =
      value.lhs ??
      value.left ??
      value.non_terminal;

    const rhs =
      value.rhs ??
      value.right;

    if (lhs !== undefined && rhs !== undefined) {

      let rhsText;

      if (Array.isArray(rhs)) {
        rhsText = rhs.length > 0
          ? rhs.map(formatProductionCell).join("")
          : "ε";
      } else {
        rhsText = String(rhs || "ε");
      }

      return `${lhs} -> ${rhsText}`;
    }

    // Handle other structured objects safely
    return JSON.stringify(value);
  }

  return String(value);
}


// =====================================================
// VISUAL PARSE TREE NODE
// =====================================================

function TreeNode({ node }) {

  if (!node) return null;

  const children = node.children || [];

  return (
    <li>

      <div
        className={
          children.length === 0
            ? "pv-tree-node terminal"
            : "pv-tree-node nonterminal"
        }
      >
        {node.symbol}
      </div>

      {children.length > 0 && (

        <ul>

          {children.map((child, index) => (

            <TreeNode
              key={index}
              node={child}
            />

          ))}

        </ul>

      )}

    </li>
  );
}


// =====================================================
// MAIN PARSEVIZ COMPONENT
// =====================================================

function ParseViz() {

  const [grammar, setGrammar] = useState(DEFAULT_GRAMMAR);

  const [inputString, setInputString] = useState("id+id*id");

  const [activeResult, setActiveResult] = useState("");

  const [results, setResults] = useState({});

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [selectedStep, setSelectedStep] = useState(0);


  // ===================================================
  // CALL BACKEND API
  // ===================================================

  async function runAnalysis(key, endpoint, includeInput = false) {

    if (!grammar.trim()) {
      setError("Please enter a grammar.");
      return;
    }

    setLoading(true);
    setError("");
    setActiveResult(key);
    setSelectedStep(0);

    try {

      const body = {
        grammar: grammar
      };

      if (includeInput) {
        body.input_string = inputString;
      }

      const data = await callAPI(endpoint, body);

      setResults(previous => ({
        ...previous,
        [key]: data
      }));

    } catch (err) {

      setError(err.message);

    } finally {

      setLoading(false);

    }
  }


  // ===================================================
  // AVAILABLE ANALYSIS TOOLS
  // ===================================================

  const actions = [

    {
      key: "validate",
      label: "Validate Grammar",
      endpoint: "/parseviz/validate"
    },

    {
      key: "recursion",
      label: "Eliminate Left Recursion",
      endpoint: "/parseviz/left-recursion"
    },

    {
      key: "factoring",
      label: "Left Factoring",
      endpoint: "/parseviz/left-factoring"
    },

    {
      key: "firstFollow",
      label: "Calculate FIRST & FOLLOW",
      endpoint: "/parseviz/first-follow"
    },

    {
      key: "table",
      label: "Generate LL(1) Table",
      endpoint: "/parseviz/parsing-table"
    },

    {
      key: "parse",
      label: "Parse Input",
      endpoint: "/parseviz/parse",
      includeInput: true
    }

  ];


  const data = results[activeResult];


  // ===================================================
  // 1. GRAMMAR VALIDATION
  // ===================================================

  function renderValidation() {

    return (

      <div className="pv-card">

        <h2>Grammar Validation</h2>

        <p className={data.valid ? "pv-success" : "pv-error"}>
          {data.valid
            ? "Grammar is valid"
            : "Grammar is invalid"}
        </p>

        <p>
          <strong>Start symbol:</strong>{" "}
          {data.start_symbol || "Not available"}
        </p>

        <p>
          <strong>Non-terminals:</strong>{" "}
          {JSON.stringify(data.non_terminals)}
        </p>

        <p>
          <strong>Terminals:</strong>{" "}
          {JSON.stringify(data.terminals)}
        </p>

        {data.errors?.map((item, index) => (
          <p className="pv-error" key={index}>
            {String(item)}
          </p>
        ))}

        {data.warnings?.map((item, index) => (
          <p className="pv-warning" key={index}>
            {String(item)}
          </p>
        ))}

      </div>

    );
  }


  // ===================================================
  // 2. LEFT RECURSION AND LEFT FACTORING
  // ===================================================

  function renderTransformation() {

    const isRecursion = activeResult === "recursion";

    const found = isRecursion
      ? data.has_left_recursion
      : data.has_left_factoring;

    return (

      <div className="pv-card">

        <h2>
          {isRecursion
            ? "Left Recursion Elimination"
            : "Left Factoring"}
        </h2>

        <p className={data.valid ? "pv-success" : "pv-error"}>

          {!data.valid
            ? "Invalid grammar"
            : found
              ? "Transformation performed"
              : "No transformation required"}

        </p>


        <h3>Original Grammar</h3>

        <pre>
          {data.original_grammar}
        </pre>


        {data.valid && (

          <>

            <h3>Transformation Steps</h3>

            {data.steps?.length > 0

              ? data.steps.map((step, index) => (

                  <pre key={index}>
                    {typeof step === "object"
                      ? JSON.stringify(step, null, 2)
                      : step}
                  </pre>

                ))

              : <p>No transformation steps.</p>

            }


            <h3>Transformed Grammar</h3>

            <pre>
              {data.transformed_grammar}
            </pre>

          </>

        )}


        {data.errors?.map((item, index) => (

          <p className="pv-error" key={index}>
            {String(item)}
          </p>

        ))}

      </div>

    );
  }


  // ===================================================
  // 3. FIRST AND FOLLOW SETS
  // ===================================================

  function renderFirstFollow() {

    return (

      <div className="pv-card">

        <h2>FIRST and FOLLOW Sets</h2>

        {!data.valid && (

          <p className="pv-error">
            Invalid grammar. Cannot calculate sets.
          </p>

        )}


        {data.valid && (

          <>

            <h3>FIRST Sets</h3>

            <div className="pv-set-grid">

              {Object.entries(data.first || {}).map(
                ([symbol, values]) => (

                  <div className="pv-set" key={symbol}>

                    <strong>
                      FIRST({symbol})
                    </strong>

                    <p>
                      {"{ "}
                      {values.join(", ")}
                      {" }"}
                    </p>

                  </div>

                )
              )}

            </div>


            <h3>FOLLOW Sets</h3>

            <div className="pv-set-grid">

              {Object.entries(data.follow || {}).map(
                ([symbol, values]) => (

                  <div className="pv-set" key={symbol}>

                    <strong>
                      FOLLOW({symbol})
                    </strong>

                    <p>
                      {"{ "}
                      {values.join(", ")}
                      {" }"}
                    </p>

                  </div>

                )
              )}

            </div>


            <h3>FIRST Explanations</h3>

            <pre>
              {JSON.stringify(
                data.first_explanations || [],
                null,
                2
              )}
            </pre>


            <h3>FOLLOW Explanations</h3>

            <pre>
              {JSON.stringify(
                data.follow_explanations || [],
                null,
                2
              )}
            </pre>

          </>

        )}

      </div>

    );
  }


  // ===================================================
  // 4. LL(1) PARSING TABLE
  // ===================================================

  function renderTable() {

    const table = data.table || {};

    const rows = data.rows || Object.keys(table);

    const columns = data.columns || [];


    return (

      <div className="pv-card">

        <h2>LL(1) Parsing Table</h2>

        <p className={
          data.is_ll1
            ? "pv-success"
            : "pv-error"
        }>

          {data.is_ll1
            ? "Grammar is LL(1)"
            : "Grammar is NOT LL(1)"}

        </p>


        <div className="pv-scroll">

          <table>

            <thead>

              <tr>

                <th>Non-terminal</th>

                {columns.map(column => (

                  <th key={column}>
                    {column}
                  </th>

                ))}

              </tr>

            </thead>


            <tbody>

              {rows.map(row => (

                <tr key={row}>

                  <th>{row}</th>

                  {columns.map(column => {

                    const value = table[row]?.[column];

                    const cell =
                      value === null ||
                      value === undefined ||
                      (Array.isArray(value) && value.length === 0)
                        ? "ERROR"
                        : formatProductionCell(value);


                    return (

                      <td
                        key={column}
                        className={
                          cell === "ERROR"
                            ? "pv-error-cell"
                            : ""
                        }
                      >

                        {cell}

                      </td>

                    );

                  })}

                </tr>

              ))}

            </tbody>

          </table>

        </div>


        <h3>Conflict Analysis</h3>

        {data.conflicts?.length > 0

          ? (

              <pre>
                {JSON.stringify(
                  data.conflicts,
                  null,
                  2
                )}
              </pre>

            )

          : (

              <p className="pv-success">
                No conflicts found.
              </p>

            )

        }


        <p>

          <strong>
            Empty/error entries:
          </strong>{" "}

          {data.error_entries?.length ?? 0}

        </p>

      </div>

    );
  }


  // ===================================================
  // 5. PREDICTIVE PARSING
  // ===================================================

  function renderParsing() {

    const trace = data.trace || [];

    const currentStep = trace[selectedStep];


    return (

      <div className="pv-card">

        <h2>Predictive Parsing Result</h2>


        {data.accepted && (

          <p className="pv-success">
            Input string ACCEPTED!
          </p>

        )}


        {data.accepted === false && (

          <p className="pv-error">
            Input string REJECTED!
          </p>

        )}


        {!data.valid && (

          <p className="pv-error">
            Invalid grammar.
          </p>

        )}


        {data.error && (

          <p className="pv-error">
            {data.error}
          </p>

        )}


        {/* INTERACTIVE PARSING STEPS */}

        {trace.length > 0 && (

          <>

            <h3>Interactive Parsing Steps</h3>

            <div className="pv-navigation">

              <button
                disabled={selectedStep === 0}
                onClick={() => setSelectedStep(selectedStep - 1)}
              >
                Previous
              </button>


              <strong>
                Step {selectedStep + 1} / {trace.length}
              </strong>


              <button
                disabled={selectedStep >= trace.length - 1}
                onClick={() => setSelectedStep(selectedStep + 1)}
              >
                Next
              </button>

            </div>


            {currentStep && (

              <div className="pv-current-step">

                <p>
                  <strong>Stack:</strong>{" "}
                  {currentStep.stack}
                </p>

                <p>
                  <strong>Remaining input:</strong>{" "}
                  {currentStep.remaining_input}
                </p>

                <p>
                  <strong>Action:</strong>{" "}
                  {currentStep.action}
                </p>

              </div>

            )}


            {/* COMPLETE PARSING TRACE */}

            <div className="pv-scroll">

              <table>

                <thead>

                  <tr>
                    <th>Step</th>
                    <th>Stack</th>
                    <th>Remaining Input</th>
                    <th>Action</th>
                  </tr>

                </thead>


                <tbody>

                  {trace.map((step, index) => (

                    <tr
                      key={index}
                      className={
                        index === selectedStep
                          ? "pv-active-row"
                          : ""
                      }
                    >

                      <td>
                        {step.step ?? index + 1}
                      </td>

                      <td>
                        {step.stack}
                      </td>

                      <td>
                        {step.remaining_input}
                      </td>

                      <td>
                        {step.action}
                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>

            </div>

          </>

        )}


        {/* VISUAL PARSE TREE */}

        {data.accepted && data.parse_tree && (

          <>

            <h3>Visual Parse Tree</h3>

            <div className="pv-tree-container">

              <ul>

                <TreeNode node={data.parse_tree} />

              </ul>

            </div>

          </>

        )}


        {/* ERROR LOCATION */}

        {!data.accepted &&
          data.error_position !== undefined && (

            <div className="pv-error-location">

              <h3>Error Location</h3>

              <p>
                Error position (0-based token index):{" "}
                {data.error_position}
              </p>

            </div>

          )}

      </div>

    );
  }


  // ===================================================
  // DISPLAY SELECTED RESULT
  // ===================================================

  function renderResult() {

    if (!data) return null;

    switch (activeResult) {

      case "validate":
        return renderValidation();

      case "recursion":
      case "factoring":
        return renderTransformation();

      case "firstFollow":
        return renderFirstFollow();

      case "table":
        return renderTable();

      case "parse":
        return renderParsing();

      default:
        return null;

    }
  }


  // ===================================================
  // MAIN USER INTERFACE
  // ===================================================

  return (

    <div className="parseviz-container">

      {/* HEADER */}

      <header className="pv-header">

        <h1>
          ParseViz - Interactive LL(1) Grammar Studio
        </h1>

        <p>
          Explore CFG, left recursion, left factoring,
          FIRST, FOLLOW, LL(1) parsing tables and predictive parsing.
        </p>

      </header>


      {/* GRAMMAR EDITOR */}

      <section className="pv-card">

        <h2>1. Enter Grammar</h2>

        <textarea
          className="pv-grammar"
          value={grammar}
          onChange={event => setGrammar(event.target.value)}
          rows="8"
          placeholder="Enter your CFG grammar here"
        />


        <div className="pv-buttons">

          <button
            onClick={() => {

              setGrammar(DEFAULT_GRAMMAR);
              setInputString("id+id*id");

              setResults({});
              setError("");
              setActiveResult("");
              setSelectedStep(0);

            }}
          >
            Load Example
          </button>


          <button
            onClick={() => {

              setGrammar("");
              setResults({});
              setError("");
              setActiveResult("");
              setSelectedStep(0);

            }}
          >
            Clear
          </button>

        </div>


        <h3>Input String</h3>

        <input
          className="pv-input"
          value={inputString}
          onChange={event => setInputString(event.target.value)}
          placeholder="Example: id+id*id"
        />


        <p className="pv-help">
          Enter epsilon as "epsilon" in the grammar when needed.
        </p>

      </section>


      {/* ANALYSIS TOOLS */}

      <section className="pv-card">

        <h2>2. Analysis Tools</h2>

        <div className="pv-action-grid">

          {actions.map(action => (

            <button
              key={action.key}
              disabled={loading}

              className={
                activeResult === action.key
                  ? "active"
                  : ""
              }

              onClick={() => runAnalysis(
                action.key,
                action.endpoint,
                action.includeInput || false
              )}
            >

              {loading && activeResult === action.key
                ? "Processing..."
                : action.label}

            </button>

          ))}

        </div>

      </section>


      {/* ERROR MESSAGE */}

      {error && (

        <div className="pv-error-box">

          <strong>Error:</strong>{" "}
          {error}

        </div>

      )}


      {/* ANALYSIS RESULTS */}

      <section className="pv-output">

        <h2>3. Analysis Results</h2>


        {loading && (

          <p>
            Processing your grammar...
          </p>

        )}


        {!loading && data && renderResult()}


        {!loading && !data && !error && (

          <p className="pv-empty">
            Select an analysis tool to view its results.
          </p>

        )}

      </section>


      {/* FOOTER */}

      <footer className="pv-footer">

        ParseViz | Interactive LL(1) Grammar Practice Studio

      </footer>

    </div>

  );

}


export default ParseViz;
