# Abre o .docx no Word, atualiza o sumário e grava o .docx e o .pdf finais.
# Uso: powershell -File tools/tcc/word.ps1 <entrada.docx> <saida.docx> <saida.pdf>
param([string]$Entrada, [string]$Saida, [string]$Pdf)
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {
  $doc = $w.Documents.Open((Resolve-Path $Entrada).Path)
  $doc.Repaginate()
  $doc.TablesOfContents | ForEach-Object { $_.Update() }
  $doc.SaveAs2([IO.Path]::GetFullPath($Saida), 16)
  $doc.ExportAsFixedFormat([IO.Path]::GetFullPath($Pdf), 17)
  "páginas: " + $doc.ComputeStatistics(2)
  $doc.Close(0)
} finally { $w.Quit() }
