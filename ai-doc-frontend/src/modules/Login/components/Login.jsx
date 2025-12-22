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
  FormControlLabel,
  Checkbox,
  Link,
  Avatar,
} from "@mui/material";
import {
  Visibility,
  VisibilityOff,
  Description as DescriptionIcon,
} from "@mui/icons-material";
import { useLogin } from "../hooks/useLogin";

export default function Login() {
  const {
    email,
    setEmail,
    password,
    setPassword,
    loading,
    error,
    showRegisterPrompt,
    handleLogin,
    goToRegister,
  } = useLogin();

  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    handleLogin();
    console.log("Remember me:", rememberMe);
  };

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
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
            Sign in to access your documents
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

              {/* error message from hook */}
              {error && (
                <Typography variant="body2" color="error">
                  {error}
                </Typography>
              )}

              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Remember me"
                />
                <Link
                  href="#"
                  underline="hover"
                  sx={{ color: "primary.main" }}
                >
                  Forgot password?
                </Link>
              </Box>

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
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  "&:hover": {
                    background:
                      "linear-gradient(135deg, #5568d3 0%, #65408b 100%)",
                  },
                }}
              >
                {loading ? "Signing in..." : "Sign In"}
              </Button>
            </Box>
          </form>

          {/* Show register prompt only when backend suggests it */}
            <Box sx={{ mt: 3, textAlign: "center" }}>
              <Typography variant="body2" color="text.secondary">
                Don't have an account?{" "}
                <Link
                  underline="hover"
                  sx={{ color: "primary.main", cursor: "pointer" }}
                  onClick={goToRegister}
                >
                  Sign up
                </Link>
              </Typography>
            </Box>
        </Paper>

        <Typography
          variant="body2"
          sx={{
            textAlign: "center",
            mt: 4,
            color: "rgba(255, 255, 255, 0.8)",
          }}
        >
          © 2025 Document Reader. All rights reserved.
        </Typography>
      </Container>
    </Box>
  );
}
