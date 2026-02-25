import { useState, useEffect } from "react";
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  Avatar,
  IconButton,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  AppBar,
  Toolbar,
  CircularProgress,
  Alert,
} from "@mui/material";
import {
  Description as DescriptionIcon,
  UploadFile,
  Logout,
  PictureAsPdf,
  Article,
  InsertDriveFile,
  CloudUpload,
  Download,
  CompareArrows,
} from "@mui/icons-material";
import { useAuth } from "../../auth/AuthProvider";
import { useNavigate } from "react-router-dom";

export default function MainPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const API_BASE = import.meta.env.VITE_API_BASE;

  // Fetch documents on load
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/documents`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents);
      }
    } catch (err) {
      console.error("Error fetching documents:", err);
    }
  };

  const handleFileUpload = () => {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = ".pdf";
    fileInput.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      setUploading(true);
      setError("");

      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch(`${API_BASE}/upload`, {
          method: "POST",
          body: formData,
          credentials: "include",
        });

        const data = await res.json();

        if (res.ok) {
            // Refresh list
            fetchDocuments();
        } else {
            setError(data.error || "Upload failed");
        }
      } catch (err) {
        console.error("Upload error:", err);
        setError("Network error during upload");
      } finally {
        setUploading(false);
      }
    };
    fileInput.click();
  };

  const handleDownloadExcel = async (filename) => {
      try {
        window.open(`${API_BASE}/download/${filename}`, '_blank');
      } catch (err) {
          console.error("Download error:", err);
      }
  }

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    switch (ext) {
      case "pdf":
        return <PictureAsPdf sx={{ fontSize: 40, color: "#d32f2f" }} />;
      case "xls":
      case "xlsx":
        return <Article sx={{ fontSize: 40, color: "#2e7d32" }} />;
      default:
        return <InsertDriveFile sx={{ fontSize: 40, color: "#757575" }} />;
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#f5f5f5" }}>
      {/* App Bar */}
      <AppBar
        position="static"
        sx={{
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        }}
      >
        <Toolbar>
          <Avatar sx={{ bgcolor: "white", color: "#667eea", mr: 2 }}>
            <DescriptionIcon />
          </Avatar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            AI Bank Statement Analyzer
          </Typography>
          <Button
            variant="outlined"
            startIcon={<CompareArrows />}
            onClick={() => navigate("/compare")}
            sx={{
              color: "white",
              borderColor: "rgba(255,255,255,0.5)",
              textTransform: "none",
              mr: 2,
              "&:hover": { borderColor: "white", bgcolor: "rgba(255,255,255,0.1)" },
            }}
          >
            Compare Docs
          </Button>
          <Typography variant="body2" sx={{ mr: 2 }}>
            {user?.email}
          </Typography>
          <IconButton color="inherit" onClick={logout}>
            <Logout />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Welcome */}
        <Box sx={{ mb: 4, color: "#667eea" }}>
          <Typography variant="h4">Welcome back, {user?.name || 'User'}!</Typography>
          <Typography>
            Upload bank statements and extract transactions automatically for audit & compliance
          </Typography>
        </Box>

        {error && (
            <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
        )}

        {/* Upload */}
        <Paper
          sx={{
            p: 4,
            mb: 4,
            borderRadius: 3,
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            color: "white",
            textAlign: "center",
          }}
        >
          <CloudUpload sx={{ fontSize: 64, mb: 2 }} />
          <Typography variant="h5">Upload Bank Statements</Typography>
          <Typography sx={{ mb: 3 }}>
            Supports scanned, unformatted & multi-bank statements
          </Typography>
          
          <Button
            variant="contained"
            size="large"
            startIcon={uploading ? <CircularProgress size={20} color="inherit"/> : <UploadFile />}
            onClick={handleFileUpload}
            disabled={uploading}
            sx={{
              bgcolor: "white",
              color: "#667eea",
              textTransform: "none",
              px: 4,
              py: 1.5,
            }}
          >
            {uploading ? "Processing..." : "Upload Statement"}
          </Button>
          
          <Typography variant="caption" display="block" sx={{ mt: 2 }}>
            PDF supported (Max 50MB)
          </Typography>
        </Paper>

        {/* Documents */}
        <Typography variant="h5" gutterBottom sx={{ color: "#667eea" }}>
          Uploaded Statements
        </Typography>

        {documents.length === 0 ? (
             <Typography color="text.secondary">No documents uploaded yet.</Typography>
        ) : (
        <Grid container spacing={2}>
          {documents.map((doc) => (
            <Grid item xs={12} md={4} key={doc._id}>
              <Card sx={{ height: "100%", borderRadius: 2 }}>
                <CardContent>
                  <Box sx={{ display: "flex", mb: 2 }}>
                    {getFileIcon(doc.original_name)}
                    <Box sx={{ ml: 2, overflow: 'hidden' }}>
                      <Typography variant="h6" noWrap title={doc.original_name}>
                        {doc.original_name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {doc.bank} • {new Date(doc.upload_date).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </Box>

                  {doc.status === "completed" ? (
                    <>
                      <Chip
                        label={`✔ ${doc.transaction_count} transactions`}
                        color="success"
                        size="small"
                        sx={{ mb: 1, mr: 1 }}
                      />
                      <Chip
                        label={`Confidence ${(doc.confidence * 100).toFixed(0)}%`}
                        color="primary"
                        size="small"
                      />
                    </>
                  ) : (
                    <Chip
                      label={doc.status}
                      color="warning"
                      size="small"
                    />
                  )}
                </CardContent>

                <CardActions sx={{ justifyContent: "space-between" }}>
                  <Button
                    startIcon={<Download />}
                    onClick={() => handleDownloadExcel(doc.excel_filename)}
                    disabled={!doc.excel_filename}
                    sx={{ textTransform: "none" }}
                  >
                    Download Excel
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
        )}
      </Container>
    </Box>
  );
}
