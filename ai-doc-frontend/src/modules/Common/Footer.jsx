import { Box, Typography } from "@mui/material";

export default function Footer() {
  return (
    <Box 
      sx={{ 
        bgcolor: "#111827",
        color: "white",
        py: 2,
        textAlign: "center"
      }}
    >
      <Typography variant="body2">
        © {new Date().getFullYear()} AI Document Intelligence — All rights reserved.
      </Typography>
    </Box>
  );
};
