import { Routes, Route } from "react-router-dom";
import "./App.css";
import Login from "./modules/Login/components/Login";
import Register from "./modules/Login/components/Register";
import MainPage from "./modules/Document/MainPage";

function App() {
  return (
    <>
      <Routes>
        <Route 
          path="/login" 
          element={
              <Login />
          } 
        />
        <Route path="/register" element={<Register />} />
        <Route path="/main" element={<MainPage />} />
        <Route path="*" element={<Login />} />
      </Routes>
    </>
  );
}

export default App;
