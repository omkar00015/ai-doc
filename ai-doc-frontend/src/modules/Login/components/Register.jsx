import { useState } from "react";
import {
  Box,
  Container,
  TextField,
  Button,
  Typography,
  Paper,
  InputAdornment,
  IconButton,
  Avatar,
  Link,
} from "@mui/material";
import {
  Visibility,
  VisibilityOff,
  Description as DescriptionIcon,
} from "@mui/icons-material";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../../../auth/AuthProvider";

export default function RegisterPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const auth = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState(
    // prefill email if passed from login
    (location.state && location.state.email) || ""
  );
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const { setUser } = auth || { setUser: () => {} };

  const handleRegister = async () => {
    if (!auth) {
      console.error("Auth not initialized");
      setError("Authentication system not ready");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE}/auth/register`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: fullName, email, password }),
      });

      const json = await res.json();

      if (!res.ok) {
        setError(json.message || "Registration failed");
      } else {
        // backend sets cookie and returns user — set context and redirect
        setUser(json.user);
        navigate("/dashboard");
      }
    } catch (e) {
      console.error(e);
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleRegister();
  };

  const handleClickShowPassword = () => {
    setShowPassword((prev) => !prev);
  };

  const handleClickShowConfirmPassword = () => {
    setShowConfirmPassword((prev) => !prev);
  };

  const onNavigateToLogin = () => {
    navigate("/login");
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        padding: 2,
      }}
    >
      <Container maxWidth="sm">
        <Box sx={{ textAlign: "center", mb: 4 }}>
          <Avatar
            sx={{
              width: 64,
              height: 64,
              bgcolor: "white",
              color: "#667eea",
              margin: "0 auto",
              mb: 2,
            }}
          >
            <DescriptionIcon sx={{ fontSize: 36 }} />
          </Avatar>
          <Typography variant="h4" component="h1" sx={{ color: "white", mb: 1 }}>
            Document Reader
          </Typography>
          <Typography variant="body1" sx={{ color: "rgba(255, 255, 255, 0.9)" }}>
            Create an account to get started
          </Typography>
        </Box>

        <Paper
          elevation={8}
          sx={{
            padding: 4,
            borderRadius: 3,
          }}
        >
          <form onSubmit={handleSubmit}>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
              <TextField
                label="Full Name"
                type="text"
                fullWidth
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                variant="outlined"
                placeholder="John Doe"
              />

              <TextField
                label="Email Address"
                type="email"
                fullWidth
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                variant="outlined"
                placeholder="you@example.com"
              />

              <TextField
                label="Password"
                type={showPassword ? "text" : "password"}
                fullWidth
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                variant="outlined"
                placeholder="Enter your password"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={handleClickShowPassword}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />

              <TextField
                label="Confirm Password"
                type={showConfirmPassword ? "text" : "password"}
                fullWidth
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                variant="outlined"
                placeholder="Confirm your password"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle confirm password visibility"
                        onClick={handleClickShowConfirmPassword}
                        edge="end"
                      >
                        {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />

              {/* Error message */}
              {error && (
                <Typography variant="body2" color="error">
                  {error}
                </Typography>
              )}

              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                disabled={loading}
                sx={{
                  py: 1.5,
                  textTransform: "none",
                  fontSize: "1rem",
                  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  "&:hover": {
                    background: "linear-gradient(135deg, #5568d3 0%, #65408b 100%)",
                  },
                }}
              >
                {loading ? "Creating account..." : "Create Account"}
              </Button>
            </Box>
          </form>

          <Box sx={{ mt: 3, textAlign: "center" }}>
            <Typography variant="body2" color="text.secondary">
              Already have an account?{" "}
              <Link
                component="button"
                type="button"
                onClick={onNavigateToLogin}
                underline="hover"
                sx={{ color: "primary.main", cursor: "pointer" }}
              >
                Sign in
              </Link>
            </Typography>
          </Box>
        </Paper>

        <Typography
          variant="body2"
          sx={{ textAlign: "center", mt: 4, color: "rgba(255, 255, 255, 0.8)" }}
        >
          © 2025 Document Reader. All rights reserved.
        </Typography>
      </Container>
    </Box>
  );
}
