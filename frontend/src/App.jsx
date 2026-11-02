
import { useState } from "react";
import "./App.css";
import ParseViz from "./parseviz/ParseViz";


// =====================================================
// ORIGINAL CFG ANALYZER - PARSE TREE NODE
// =====================================================

function TreeNode({ node }) {
  return (
    <li>
      <div className="parse-node">
        {node.symbol}
      </div>

      {node.children && node.children.length > 0 && (
        <ul>
          {node.children.map((child, index) => (
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
// ORIGINAL CFG ANALYZER - PARSE TREE
// =====================================================

function ParseTree({ tree, number }) {
  return (
    <div className="single-tree-card">
      <h3>Parse Tree {number}</h3>

      <div className="tree-scroll">
        <div className="tree-drawing">
          <ul>
            <TreeNode node={tree} />
          </ul>
        </div>
      </div>
    </div>
  );
}


// =====================================================
// ORIGINAL CFG AMBIGUITY ANALYZER
// =====================================================

function OriginalAnalyzer() {

  const [grammar, setGrammar] = useState("");
  const [inputString, setInputString] = useState("");

  const [result, setResult] = useState("");
  const [error, setError] = useState("");

  const [parseTrees, setParseTrees] = useState([]);
  const [parseTreeCount, setParseTreeCount] = useState(null);
  const [ambiguous, setAmbiguous] = useState(null);

  const analyzeGrammar = async () => {

    setResult("");
    setError("");
    setParseTrees([]);
    setParseTreeCount(null);
    setAmbiguous(null);

    if (!grammar.trim()) {
      setError("Please enter a CFG grammar.");
      return;
    }

    try {

      const response = await fetch(
        "http://127.0.0.1:5000/analyze",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            grammar: grammar,
            input_string: inputString
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Grammar analysis failed.");
        return;
      }

      setResult(data.output || "");
      setParseTreeCount(data.parse_tree_count || 0);
      setAmbiguous(data.ambiguous_for_input || false);
      setParseTrees(data.parse_trees || []);

    } catch (err) {

      setError(
        "Could not connect to Flask backend. Make sure Flask is running."
      );

    }
  };


  return (
    <div className="container">

      <h1>
        CFG Ambiguity Detection & Parse Tree Analyzer
      </h1>

      <p className="description">
        Enter a context-free grammar and input string
        to analyze parsing and ambiguity.
      </p>


      {/* CFG GRAMMAR */}

      <div className="input-card">

        <h2>CFG Grammar</h2>

        <textarea
          rows="8"
          placeholder={`Example:

E->E+E|E*E|id`}
          value={grammar}
          onChange={(e) => setGrammar(e.target.value)}
        />

      </div>


      {/* INPUT STRING */}

      <div className="input-card">

        <h2>Input String</h2>

        <input
          type="text"
          className="input-string"
          placeholder="Example: id+id*id"
          value={inputString}
          onChange={(e) => setInputString(e.target.value)}
        />

      </div>


      {/* ANALYZE BUTTON */}

      <button onClick={analyzeGrammar}>
        Analyze Grammar
      </button>


      {/* AMBIGUITY RESULT */}

      {ambiguous !== null && (

        <div className="analysis-card">

          <h2>Ambiguity Analysis</h2>

          <p>
            <strong>Input String:</strong> {inputString}
          </p>

          <p>
            <strong>Parse Trees Found:</strong> {parseTreeCount}
          </p>

          <p
            className={
              ambiguous
                ? "ambiguous"
                : parseTreeCount === 0
                ? "no-tree"
                : "not-ambiguous"
            }
          >

            <strong>Result:</strong>{" "}

            {ambiguous
              ? "YES - Multiple parse trees found"
              : parseTreeCount === 0
              ? "No valid parse tree found for this input"
              : "NO - Only one parse tree found"
            }

          </p>

        </div>

      )}


      {/* PARSER RESULT */}

      {result && (

        <div className="result">

          <h2>Parser Result</h2>

          <pre>{result}</pre>

        </div>

      )}


      {/* ERROR */}

      {error && (

        <div className="error">

          <h2>Error</h2>

          <pre>{error}</pre>

        </div>

      )}


      {/* ALL PARSE TREES */}

      {parseTrees.length > 0 && (

        <div className="all-trees-section">

          <h2>All Possible Parse Trees</h2>

          <div className="all-trees">

            {parseTrees.map((tree, index) => (

              <ParseTree
                key={index}
                tree={tree}
                number={index + 1}
              />

            ))}

          </div>

        </div>

      )}

    </div>
  );
}


// =====================================================
// MAIN APPLICATION
// =====================================================

function App() {

  const [activeTool, setActiveTool] = useState("analyzer");


  return (

    <div>

      {/* APPLICATION NAVIGATION */}

      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "12px",
          padding: "20px",
          flexWrap: "wrap"
        }}
      >

        <button
          type="button"
          onClick={() => setActiveTool("analyzer")}
          style={{
            backgroundColor:
              activeTool === "analyzer" ? "#174ea6" : "#64748b",
            color: "white",
            padding: "12px 22px",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: "600"
          }}
        >
          CFG Ambiguity Analyzer
        </button>


        <button
          type="button"
          onClick={() => setActiveTool("parseviz")}
          style={{
            backgroundColor:
              activeTool === "parseviz" ? "#174ea6" : "#64748b",
            color: "white",
            padding: "12px 22px",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            fontWeight: "600"
          }}
        >
          ParseViz - LL(1) Studio
        </button>

      </div>


      {/* DISPLAY SELECTED TOOL */}

      {activeTool === "analyzer" ? (
        <OriginalAnalyzer />
      ) : (
        <ParseViz />
      )}

    </div>

  );

}


export default App;
