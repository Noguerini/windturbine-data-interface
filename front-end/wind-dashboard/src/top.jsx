import {useState, useEffect} from 'react'
import { io } from "socket.io-client";

import classes from './top.module.css'

import ControlPanel from './panels/controlpanel.jsx'
import ViewingPanel from './panels/viewingpanel.jsx'

function App() {
    const [timestamp, setTimestamp] = useState(0);
    const [channels, setChannels] = useState([]);

    useEffect(() => {
        const socket = io("http://localhost:15641", {
            transports: ["websocket"],
        });

        socket.on("connect", () => {
            console.log("Connected to data server");
        });

        socket.on("data", (payload) => {
            setTimestamp(payload.timestamp);
            setChannels(payload.channels);
        });

        socket.on("disconnect", () => {
            console.log("Disconnected from server");
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    return (
        <div className={classes.container}>
            <ControlPanel/>
            <ViewingPanel timestamp={timestamp} channels={channels} />
        </div>
    )
}

export default App