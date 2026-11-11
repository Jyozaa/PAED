#!/usr/bin/env Rscript
# Conditional established-package estimators. The present evidence fails both
# eligibility gates. No R packages are needed to execute those early exits.
args <- commandArgs(trailingOnly=TRUE)
root <- if (length(args)) args[[1]] else "."
a <- read.csv(file.path(root,"results","auroc_estimates.csv"), stringsAsFactors=FALSE)
d <- read.csv(file.path(root,"results","diagnostic_2x2.csv"), stringsAsFactors=FALSE)
truth <- function(x) tolower(as.character(x)) %in% c("true","1")
independent <- function(x) {
  if (anyNA(x$dependency_group) || any(!nzchar(x$dependency_group)) || anyDuplicated(x$dependency_group))
    stop("Missing/duplicated dependency groups: repeated models or potentially overlapping cohorts")
}
confirmed <- function(x, fields) {
  all(vapply(fields, function(k) k %in% names(x) && all(truth(x[[k]])), logical(1)))
}
a <- a[truth(a$pooled_eligible),,drop=FALSE]
d <- d[truth(d$pooled_eligible),,drop=FALSE]
if (!nrow(a) && !nrow(d)) {
  cat("AUROC: not statistically defensible; no eligible independent estimates.\n")
  cat("Bivariate: not statistically defensible; no eligible independent unit-verified tables.\n")
  cat("No model fitted; this is an evidence-feasibility outcome, not a technical failure.\n")
  quit(save="no",status=0)
}
if (nrow(a)) {
  independent(a)
  stopifnot(nrow(a)>=3, all(is.finite(a$se_logit_approx)),all(a$se_logit_approx>0),
            all(a$auroc>0 & a$auroc<1), all(a$evaluation!="training"),
            all(a$uncertainty_type %in% c("95%_confidence_interval","standard_error")),
            confirmed(a,c("selection_confirmed","comparability_confirmed")))
  if (!requireNamespace("metafor",quietly=TRUE)) stop("Install R metafor for eligible AUROC fitting")
  yi <- qlogis(a$auroc); vi <- a$se_logit_approx^2
  fit <- metafor::rma.uni(yi=yi,vi=vi,method="REML",test="knha",slab=a$study_id)
  # Modified H-K: prevent an interval narrower than conventional inverse-information
  # variance. This is an explicit safeguard, not undocumented manipulation of counts.
  weights <- 1/(vi+fit$tau2)
  conventional_var <- 1/sum(weights)
  se <- max(as.numeric(fit$se),sqrt(conventional_var))
  mu <- as.numeric(fit$b); crit <- qt(.975,df=nrow(a)-1)
  result <- data.frame(k=nrow(a),pooled_auroc=plogis(mu),
                       ci_lower=plogis(mu-crit*se),ci_upper=plogis(mu+crit*se),
                       tau_squared_logit=fit$tau2,Q=fit$QE,Q_p=fit$QEp,
                       se_logit_modified_hk=se,df=nrow(a)-1)
  write.csv(result,file.path(root,"results","pooled_auroc.csv"),row.names=FALSE)
  saveRDS(fit,file.path(root,"results","auroc_fit.rds"))
  svg(file.path(root,"figures","pooled_auroc.svg"),width=9,height=7)
  # Draw study estimates using genuine CI approximation and the modified-HK summary.
  metafor::forest(yi,vi=vi,slab=a$study_id,atransf=plogis,refline=NA,
                  xlab="AUROC (back-transformed logit); independent selected estimates",ylim=c(-2,nrow(a)+3))
  metafor::addpoly(mu,ci.lb=mu-crit*se,ci.ub=mu+crit*se,row=-1,atransf=plogis,
                   mlab="REML, modified Hartung-Knapp")
  dev.off()
  capture.output(summary(fit),file=file.path(root,"reports","auroc_model_diagnostics.txt"))
}
if (nrow(d)) {
  independent(d)
  stopifnot(nrow(d)>=5,
            all(d$analysis_unit %in% c("patient","admission_independent","event_independent")),
            confirmed(d,c("selection_confirmed","comparability_confirmed","model_threshold_unit_linkage_verified")))
  counts <- as.matrix(d[,c("tp","fp","fn","tn")])
  stopifnot(all(is.finite(counts)),all(counts>=0),all(counts==floor(counts)))
  if (any(counts==0)) stop("Sparse/boundary counts: use a validated binomial HSROC; no automatic continuity correction")
  if (!requireNamespace("mada",quietly=TRUE)) stop("Install R mada for eligible bivariate fitting")
  fit <- mada::reitsma(d,TP="tp",FP="fp",FN="fn",TN="tn",method="reml",correction=0)
  covar <- vcov(fit)
  stopifnot(all(is.finite(covar)), all(eigen(covar,symmetric=TRUE)$values>0))
  b <- as.numeric(coef(fit)); se <- sqrt(diag(covar))
  stopifnot(length(b)==2,length(se)==2)
  # mada models logit sensitivity and logit false-positive rate, not specificity.
  result <- data.frame(k=nrow(d),
      sensitivity=plogis(b[1]),sensitivity_ci_lower=plogis(b[1]-qnorm(.975)*se[1]),
      sensitivity_ci_upper=plogis(b[1]+qnorm(.975)*se[1]),
      specificity=plogis(-b[2]),specificity_ci_lower=plogis(-b[2]-qnorm(.975)*se[2]),
      specificity_ci_upper=plogis(-b[2]+qnorm(.975)*se[2]))
  write.csv(result,file.path(root,"results","pooled_diagnostic.csv"),row.names=FALSE)
  saveRDS(fit,file.path(root,"results","diagnostic_fit.rds"))
  svg(file.path(root,"figures","hsroc_fitted.svg"),width=8,height=7)
  plot(fit,main="Fitted bivariate summary ROC: independent eligible datasets")
  dev.off()
  capture.output(summary(fit),file=file.path(root,"reports","diagnostic_model_diagnostics.txt"))
}
capture.output(sessionInfo(),file=file.path(root,"reports","R_session_info.txt"))
