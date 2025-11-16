import {useState} from 'react'

function App() {
    const [timestamp, setTimestamp] = useState(0)

    return (
        <>
            <h1>Hello, World!</h1>
            <h2>Timestamp: {timestamp}</h2>
        </>
    )
}

export default App