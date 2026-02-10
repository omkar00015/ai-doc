import { useState } from "react";
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  Avatar,
  IconButton,
  Grid,
  Chip,
  AppBar,
  Toolbar,
  CircularProgress,
  Alert,
  LinearProgress,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Tooltip,
} from "@mui/material";
import {
  Description as DescriptionIcon,
  CompareArrows,
  UploadFile,
  Logout,
  CloudUpload,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  ExpandMore,
  ArrowBack,
  Info,
} from "@mui/icons-material";
import { useAuth } from "../../auth/AuthProvider";
import { useNavigate } from "react-router-dom";

const STATUS_CONFIG = {
  match: {
    color: "#2e7d32",
    bg: "#e8f5e9",
    label: "Match",
    icon: <CheckCircle fontSize="small" />,
  },
  modified: {
    color: "#ed6c02",
    bg: "#fff3e0",
    label: "Modified",
    icon: <Warning fontSize="small" />,
  },
  missing_in_b: {
    color: "#d32f2f",
    bg: "#ffebee",
    label: "Missing in Doc B",
    icon: <ErrorIcon fontSize="small" />,
  },
  missing_in_a: {
    color: "#9c27b0",
    bg: "#f3e5f5",
    label: "Missing in Doc A",
    icon: <ErrorIcon fontSize="small" />,
  },
};

export default function ComparePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const API_BASE = import.meta.env.VITE_API_BASE;

  const [fileA, setFileA] = useState(null);
  const [fileB, setFileB] = useState(null);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [filter, setFilter] = useState("all");

  const handleFilePick = (setter) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".pdf";
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) {
        setter(file);
        setResult(null);
        setError("");
      }
    };
    input.click();
  };

  const handleCompare = async () => {
    if (!fileA || !fileB) {
      setError("Please upload both documents before comparing.");
      return;
    }

    setComparing(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file_a", fileA);
    formData.append("file_b", fileB);

    try {
      const res = await fetch(`${API_BASE}/compare`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      const data = await res.json();

      if (res.ok && data.success) {
        setResult(data);
      } else {
        setError(data.error || "Comparison failed. Please try again.");
      }
    } catch (err) {
      console.error("Comparison error:", err);
      setError("Network error during comparison. Please try again.");
    } finally {
      setComparing(false);
    }
  };

  const getFilteredAlignments = () => {
    if (!result?.alignments) return [];
    if (filter === "all") return result.alignments;
    return result.alignments.filter((a) => a.status === filter);
  };

  const getSimilarityColor = (score) => {
    if (score >= 0.85) return "#2e7d32";
    if (score >= 0.5) return "#ed6c02";
    return "#d32f2f";
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
          <IconButton
            color="inherit"
            onClick={() => navigate("/main")}
            sx={{ mr: 1 }}
          >
            <ArrowBack />
          </IconButton>
          <Avatar sx={{ bgcolor: "white", color: "#667eea", mr: 2 }}>
            <CompareArrows />
          </Avatar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            AI Document Comparison
          </Typography>
          <Typography variant="body2" sx={{ mr: 2 }}>
            {user?.email}
          </Typography>
          <IconButton color="inherit" onClick={logout}>
            <Logout />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4, color: "#667eea" }}>
          <Typography variant="h4">Document Comparison</Typography>
          <Typography>
            Upload two documents to compare them using AI embeddings.
            Identify matches, modifications, and missing sections instantly.
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError("")}>
            {error}
          </Alert>
        )}

        {/* Upload Section */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* Document A */}
          <Grid item xs={12} md={5}>
            <Paper
              sx={{
                p: 3,
                borderRadius: 3,
                textAlign: "center",
                border: fileA ? "2px solid #2e7d32" : "2px dashed #667eea",
                bgcolor: fileA ? "#e8f5e9" : "white",
                cursor: "pointer",
                transition: "all 0.2s",
                "&:hover": { borderColor: "#764ba2", bgcolor: fileA ? "#c8e6c9" : "#f3e5f5" },
              }}
              onClick={() => handleFilePick(setFileA)}
            >
              {fileA ? (
                <CheckCircle sx={{ fontSize: 48, color: "#2e7d32", mb: 1 }} />
              ) : (
                <CloudUpload sx={{ fontSize: 48, color: "#667eea", mb: 1 }} />
              )}
              <Typography variant="h6" gutterBottom>
                Document A
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {fileA ? fileA.name : "Click to upload PDF"}
              </Typography>
              {fileA && (
                <Chip
                  label={`${(fileA.size / 1024).toFixed(0)} KB`}
                  size="small"
                  color="success"
                  sx={{ mt: 1 }}
                />
              )}
            </Paper>
          </Grid>

          {/* VS Divider */}
          <Grid
            item
            xs={12}
            md={2}
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Box sx={{ textAlign: "center" }}>
              <CompareArrows
                sx={{ fontSize: 48, color: "#667eea", mb: 1 }}
              />
              <Typography variant="h6" color="#667eea">
                VS
              </Typography>
            </Box>
          </Grid>

          {/* Document B */}
          <Grid item xs={12} md={5}>
            <Paper
              sx={{
                p: 3,
                borderRadius: 3,
                textAlign: "center",
                border: fileB ? "2px solid #2e7d32" : "2px dashed #667eea",
                bgcolor: fileB ? "#e8f5e9" : "white",
                cursor: "pointer",
                transition: "all 0.2s",
                "&:hover": { borderColor: "#764ba2", bgcolor: fileB ? "#c8e6c9" : "#f3e5f5" },
              }}
              onClick={() => handleFilePick(setFileB)}
            >
              {fileB ? (
                <CheckCircle sx={{ fontSize: 48, color: "#2e7d32", mb: 1 }} />
              ) : (
                <CloudUpload sx={{ fontSize: 48, color: "#667eea", mb: 1 }} />
              )}
              <Typography variant="h6" gutterBottom>
                Document B
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {fileB ? fileB.name : "Click to upload PDF"}
              </Typography>
              {fileB && (
                <Chip
                  label={`${(fileB.size / 1024).toFixed(0)} KB`}
                  size="small"
                  color="success"
                  sx={{ mt: 1 }}
                />
              )}
            </Paper>
          </Grid>
        </Grid>

        {/* Compare Button */}
        <Box sx={{ textAlign: "center", mb: 4 }}>
          <Button
            variant="contained"
            size="large"
            startIcon={
              comparing ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                <CompareArrows />
              )
            }
            onClick={handleCompare}
            disabled={!fileA || !fileB || comparing}
            sx={{
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              px: 6,
              py: 1.5,
              fontSize: "1.1rem",
              textTransform: "none",
              borderRadius: 3,
            }}
          >
            {comparing ? "Analyzing with AI..." : "Compare Documents"}
          </Button>
          {comparing && (
            <Box sx={{ mt: 2, maxWidth: 400, mx: "auto" }}>
              <LinearProgress
                sx={{
                  borderRadius: 2,
                  height: 6,
                  "& .MuiLinearProgress-bar": {
                    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  },
                }}
              />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                Extracting text, generating embeddings, computing similarity...
              </Typography>
            </Box>
          )}
        </Box>

        {/* Results */}
        {result && (
          <>
            {/* Summary Cards */}
            <Typography variant="h5" gutterBottom sx={{ color: "#667eea", mb: 2 }}>
              Comparison Results
            </Typography>

            <Grid container spacing={2} sx={{ mb: 3 }}>
              {/* Overall Similarity */}
              <Grid item xs={12} md={3}>
                <Card sx={{ borderRadius: 2, textAlign: "center" }}>
                  <CardContent>
                    <Typography variant="overline" color="text.secondary">
                      Overall Similarity
                    </Typography>
                    <Typography
                      variant="h3"
                      sx={{
                        color: getSimilarityColor(
                          result.summary.overall_similarity
                        ),
                        fontWeight: 700,
                      }}
                    >
                      {result.summary.overall_similarity_pct}%
                    </Typography>
                    <Tooltip title="Embedding method used for comparison">
                      <Chip
                        icon={<Info />}
                        label={result.embedding_method}
                        size="small"
                        variant="outlined"
                        sx={{ mt: 1 }}
                      />
                    </Tooltip>
                  </CardContent>
                </Card>
              </Grid>

              {/* Matches */}
              <Grid item xs={6} md={2.25}>
                <Card
                  sx={{
                    borderRadius: 2,
                    textAlign: "center",
                    borderLeft: "4px solid #2e7d32",
                  }}
                >
                  <CardContent>
                    <Typography variant="overline" color="text.secondary">
                      Matches
                    </Typography>
                    <Typography variant="h4" sx={{ color: "#2e7d32", fontWeight: 700 }}>
                      {result.summary.match_count}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Modified */}
              <Grid item xs={6} md={2.25}>
                <Card
                  sx={{
                    borderRadius: 2,
                    textAlign: "center",
                    borderLeft: "4px solid #ed6c02",
                  }}
                >
                  <CardContent>
                    <Typography variant="overline" color="text.secondary">
                      Modified
                    </Typography>
                    <Typography variant="h4" sx={{ color: "#ed6c02", fontWeight: 700 }}>
                      {result.summary.modified_count}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Missing in B */}
              <Grid item xs={6} md={2.25}>
                <Card
                  sx={{
                    borderRadius: 2,
                    textAlign: "center",
                    borderLeft: "4px solid #d32f2f",
                  }}
                >
                  <CardContent>
                    <Typography variant="overline" color="text.secondary">
                      Missing in B
                    </Typography>
                    <Typography variant="h4" sx={{ color: "#d32f2f", fontWeight: 700 }}>
                      {result.summary.missing_in_b_count}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* Missing in A */}
              <Grid item xs={6} md={2.25}>
                <Card
                  sx={{
                    borderRadius: 2,
                    textAlign: "center",
                    borderLeft: "4px solid #9c27b0",
                  }}
                >
                  <CardContent>
                    <Typography variant="overline" color="text.secondary">
                      Missing in A
                    </Typography>
                    <Typography variant="h4" sx={{ color: "#9c27b0", fontWeight: 700 }}>
                      {result.summary.missing_in_a_count}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Coverage & Chunks Info */}
            <Paper sx={{ p: 2, mb: 3, borderRadius: 2, bgcolor: "#f8f9ff" }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    Coverage:{" "}
                    <strong>{result.summary.coverage_pct}%</strong> of Doc A
                    sections found in Doc B
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    Doc A: <strong>{result.summary.total_chunks_a}</strong> sections
                    {" | "}Doc B: <strong>{result.summary.total_chunks_b}</strong> sections
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    Processed in{" "}
                    <strong>{result.processing_time_seconds}s</strong>
                  </Typography>
                </Grid>
              </Grid>
            </Paper>

            {/* Filter Chips */}
            <Box sx={{ mb: 2, display: "flex", gap: 1, flexWrap: "wrap" }}>
              {[
                { key: "all", label: `All (${result.alignments.length})` },
                { key: "match", label: `Matches (${result.summary.match_count})` },
                { key: "modified", label: `Modified (${result.summary.modified_count})` },
                { key: "missing_in_b", label: `Missing in B (${result.summary.missing_in_b_count})` },
                { key: "missing_in_a", label: `Missing in A (${result.summary.missing_in_a_count})` },
              ].map((f) => (
                <Chip
                  key={f.key}
                  label={f.label}
                  onClick={() => setFilter(f.key)}
                  variant={filter === f.key ? "filled" : "outlined"}
                  color={filter === f.key ? "primary" : "default"}
                  sx={{ cursor: "pointer" }}
                />
              ))}
            </Box>

            <Divider sx={{ mb: 2 }} />

            {/* Detailed Alignments */}
            {getFilteredAlignments().map((alignment, idx) => {
              const cfg = STATUS_CONFIG[alignment.status] || STATUS_CONFIG.match;
              return (
                <Accordion
                  key={idx}
                  sx={{
                    mb: 1,
                    borderLeft: `4px solid ${cfg.color}`,
                    borderRadius: "8px !important",
                    "&:before": { display: "none" },
                  }}
                >
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1.5,
                        width: "100%",
                      }}
                    >
                      <Chip
                        icon={cfg.icon}
                        label={cfg.label}
                        size="small"
                        sx={{
                          bgcolor: cfg.bg,
                          color: cfg.color,
                          fontWeight: 600,
                          minWidth: 130,
                        }}
                      />
                      <Typography
                        variant="body2"
                        sx={{
                          flexGrow: 1,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          maxWidth: "50%",
                        }}
                      >
                        {alignment.chunk_a_text
                          ? alignment.chunk_a_text.substring(0, 80) + "..."
                          : alignment.chunk_b_text
                            ? alignment.chunk_b_text.substring(0, 80) + "..."
                            : ""}
                      </Typography>
                      <Chip
                        label={`${(alignment.similarity * 100).toFixed(1)}%`}
                        size="small"
                        sx={{
                          bgcolor: getSimilarityColor(alignment.similarity) + "20",
                          color: getSimilarityColor(alignment.similarity),
                          fontWeight: 700,
                        }}
                      />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      {/* Doc A content */}
                      <Grid item xs={12} md={6}>
                        <Paper
                          sx={{
                            p: 2,
                            bgcolor: alignment.chunk_a_text ? "#fafafa" : "#ffebee",
                            borderRadius: 2,
                            minHeight: 80,
                          }}
                        >
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ fontWeight: 600 }}
                          >
                            Document A
                            {alignment.chunk_a_index !== null &&
                              ` (Section ${alignment.chunk_a_index + 1})`}
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{
                              mt: 1,
                              whiteSpace: "pre-wrap",
                              fontFamily: "monospace",
                              fontSize: "0.85rem",
                            }}
                          >
                            {alignment.chunk_a_text || (
                              <em style={{ color: "#d32f2f" }}>
                                Not present in Document A
                              </em>
                            )}
                          </Typography>
                        </Paper>
                      </Grid>
                      {/* Doc B content */}
                      <Grid item xs={12} md={6}>
                        <Paper
                          sx={{
                            p: 2,
                            bgcolor: alignment.chunk_b_text ? "#fafafa" : "#ffebee",
                            borderRadius: 2,
                            minHeight: 80,
                          }}
                        >
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ fontWeight: 600 }}
                          >
                            Document B
                            {alignment.chunk_b_index !== null &&
                              ` (Section ${alignment.chunk_b_index + 1})`}
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{
                              mt: 1,
                              whiteSpace: "pre-wrap",
                              fontFamily: "monospace",
                              fontSize: "0.85rem",
                            }}
                          >
                            {alignment.chunk_b_text || (
                              <em style={{ color: "#d32f2f" }}>
                                Not present in Document B
                              </em>
                            )}
                          </Typography>
                        </Paper>
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              );
            })}

            {getFilteredAlignments().length === 0 && (
              <Typography color="text.secondary" sx={{ textAlign: "center", py: 4 }}>
                No results match the selected filter.
              </Typography>
            )}
          </>
        )}
      </Container>
    </Box>
  );
}
