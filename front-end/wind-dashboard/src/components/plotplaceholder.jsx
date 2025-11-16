import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";

function PlotPlaceholder() {
  const plotRef = useRef(null);

  useEffect(() => {
    Plotly.newPlot(plotRef.current, [
      {
        x: [1, 2, 3],
        y: [2, 6, 3],
        type: "scatter",
        mode: "lines+markers",
      }
    ], {
      height: 200,
      margin: { t: 20, l: 40, r: 20, b: 40 },
      paper_bgcolor: "#181818",
      plot_bgcolor: "#181818",
      font: { color: "#fff" }
    }, { responsive: true });
  }, []);

  return (
    <div
    ref={plotRef}
    style={{
        width: "100%",
        height: "200px",
        border: "1px solid #ffffff", // thinner white border
        borderRadius: "8px"          // optional rounded corners
    }}
    ></div>
  );
}


export default PlotPlaceholder;