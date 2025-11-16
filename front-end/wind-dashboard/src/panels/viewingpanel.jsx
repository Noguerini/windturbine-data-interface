import classes from "./viewingPanel.module.css";
import PlotPlaceholder from "../components/plotplaceholder.jsx";

function ViewingPanel({ timestamp, channels }) {
  return (
    <div className={classes.panel}>
      <PlotPlaceholder/>
      <h2>Timestamp: {timestamp}</h2>
    </div>
  );
}

export default ViewingPanel;