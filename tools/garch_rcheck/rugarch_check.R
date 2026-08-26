# Verificacao cruzada com R (item 4 da Matriz de Validacao, Etapa 2): ajusta GARCH(1,1) e
# EGARCH(1,1) via rugarch sobre os MESMOS retornos de treino exportados por export_for_r.py,
# com especificacao equivalente a Python (media zero, inovacoes normais), para comparar os
# coeficientes estimados por MLE com os do pacote `arch`.
#
# Uso: Rscript tools/garch_rcheck/rugarch_check.R

suppressMessages(library(rugarch))

here <- dirname(sub("--file=", "", grep("--file=", commandArgs(trailingOnly = FALSE), value = TRUE)))
returns <- read.csv(file.path(here, "train_returns.csv"))$return

fit_and_print <- function(model_name, garch_order, submodel = NULL) {
  spec <- ugarchspec(
    variance.model = list(model = model_name, garchOrder = garch_order, submodel = submodel),
    mean.model = list(armaOrder = c(0, 0), include.mean = FALSE),
    distribution.model = "norm"
  )
  fit <- ugarchfit(spec, data = returns, solver = "hybrid")

  cat("\n===", model_name, ifelse(is.null(submodel), "", submodel), "===\n")
  print(coef(fit))
  cat("log-likelihood:", likelihood(fit), "\n")
  cat("convergence:", fit@fit$convergence, "(0 = ok)\n")
}

fit_and_print("sGARCH", c(1, 1))
fit_and_print("eGARCH", c(1, 1))
