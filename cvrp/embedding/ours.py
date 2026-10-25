"""Our embedder: MDS start, then SLSQP on a log-distance loss with device constraints.

Wanted: U_ab = C6 / r_ab^6 = T_ab (target couplings, T = s * b).
  pairs with T_ab > 0 : loss (log U_ab - log T_ab)^2  = 36 (log r_ab - log r*_ab)^2
                        -> every pair matched in percent terms, large and small alike
  pairs with T_ab = 0 : loss mu * (U_ab / U_ref)^2     -> pushed far apart (U_ref = smallest wanted coupling)
Constraints: r_ab >= 5 um (all pairs), |r_a| <= 38 um.
Start: classical MDS (SMACOF) on r*, pairs with T = 0 given a large distance; plus random restarts.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from sklearn.manifold import MDS

from ..hardware import C6, U_FAR, couplings, target_distances
from ..hardware import R_MIN as _R_MIN, R_MAX as _R_MAX

LOG_C6 = np.log(C6)
# optimise against limits with a 0.02 um safety margin; pulser compares strictly
R_MIN, R_MAX = _R_MIN + 0.02, _R_MAX - 0.02


def _pairs(n):
    return np.triu_indices(n, 1)


def loss_and_grad(flat, logT, want, zero, mu, u_ref):
    """Loss over coordinates; analytic gradient so SLSQP converges fast."""
    n = len(flat) // 2
    X = flat.reshape(n, 2)
    iu, ju = _pairs(n)
    diff = X[iu] - X[ju]
    r2 = (diff ** 2).sum(axis=1)
    logr = 0.5 * np.log(r2)
    # want pairs
    e = (LOG_C6 - 6 * logr) - logT  # log U - log T
    L = (e[want] ** 2).sum()
    dL_dlogr = np.zeros_like(r2)
    dL_dlogr[want] = -12 * e[want]
    # zero pairs: (U/u_ref)^2 = exp(2(logU - log u_ref))
    if zero.any():
        z = np.exp(2 * ((LOG_C6 - 6 * logr[zero]) - np.log(u_ref)))
        L += mu * z.sum()
        dL_dlogr[zero] += mu * z * (-12)
    # chain rule: d logr / dX = diff / r2
    g_pair = (dL_dlogr / r2)[:, None] * diff
    grad = np.zeros_like(X)
    np.add.at(grad, iu, g_pair)
    np.add.at(grad, ju, -g_pair)
    return L, grad.ravel()


def constraints(n):
    iu, ju = _pairs(n)

    def spacing(flat):
        X = flat.reshape(n, 2)
        return np.linalg.norm(X[iu] - X[ju], axis=1) - R_MIN

    def radius(flat):
        X = flat.reshape(n, 2)
        return R_MAX - np.linalg.norm(X, axis=1)

    return [{"type": "ineq", "fun": spacing}, {"type": "ineq", "fun": radius}]


def mds_start(rstar, far, seed):
    D = rstar.copy()
    D[~np.isfinite(D)] = far
    np.fill_diagonal(D, 0.0)
    mds = MDS(n_components=2, dissimilarity="precomputed", random_state=seed, n_init=4, normalized_stress="auto")
    return mds.fit_transform(D)


def fit_device(X: np.ndarray) -> np.ndarray:
    """Centre, then scale so the layout respects both the 5 um spacing and the 38 um radius if it can."""
    X = X - X.mean(axis=0)
    iu, ju = _pairs(len(X))
    dmin = np.linalg.norm(X[iu] - X[ju], axis=1).min()
    rad = np.linalg.norm(X, axis=1).max()
    scale = 1.0
    if dmin < R_MIN:
        scale = R_MIN / dmin * 1.02
    if rad * scale > 0.95 * R_MAX:
        scale = 0.95 * R_MAX / rad
    return X * scale


def is_legal(X: np.ndarray) -> bool:
    """Strict check against the real device limits (what pulser's validate_register does)."""
    iu, ju = _pairs(len(X))
    return bool((np.linalg.norm(X[iu] - X[ju], axis=1) >= _R_MIN).all()
                and (np.linalg.norm(X, axis=1) <= _R_MAX).all())


def _penalised(flat, logT, want, zero, mu, u_ref, w_con):
    """Same loss plus quadratic penalties for the device limits (fallback optimiser)."""
    n = len(flat) // 2
    L, g = loss_and_grad(flat, logT, want, zero, mu, u_ref)
    X = flat.reshape(n, 2)
    iu, ju = _pairs(n)
    diff = X[iu] - X[ju]
    d = np.linalg.norm(diff, axis=1)
    viol = np.maximum(0.0, R_MIN - d)
    L += w_con * (viol ** 2).sum()
    gp = (-2 * w_con * viol / np.maximum(d, 1e-9))[:, None] * diff
    G = np.zeros_like(X)
    np.add.at(G, iu, gp)
    np.add.at(G, ju, -gp)
    r = np.linalg.norm(X, axis=1)
    rv = np.maximum(0.0, r - R_MAX)
    L += w_con * (rv ** 2).sum()
    G += (2 * w_con * rv / np.maximum(r, 1e-9))[:, None] * X
    return L, g + G.ravel()


def embed(T: np.ndarray, mu: float = 1.0, restarts: int = 20, seed: int = 0, maxiter: int = 500,
          x0: np.ndarray | None = None):
    """Return (coords [n,2] in um, info). T = target coupling matrix (rad/us), zero diagonal.
    x0: optional starting layout used for the first restart (e.g. the scaled customer map)."""
    n = len(T)
    iu, ju = _pairs(n)
    Tp = T[iu, ju]
    want = Tp > U_FAR  # weaker than any coupling realisable inside the register counts as zero
    zero = ~want
    logT = np.where(want, np.log(np.where(want, Tp, 1.0)), 0.0)
    rstar = target_distances(T)
    far = 3.0 * rstar[np.isfinite(rstar)].max()
    u_ref = Tp[want].min()
    cons = constraints(n)
    rng = np.random.default_rng(seed)
    args = (logT, want, zero, mu, u_ref)
    best, best_x, n_feas, diag = np.inf, None, 0, []
    for t in range(restarts):
        if t == 0 and x0 is not None:
            start = np.asarray(x0, float)
        elif t < max(1, restarts // 2):
            start = mds_start(rstar, far, seed + t)
        else:
            start = rng.uniform(-far, far, (n, 2))
        x0 = fit_device(start)
        res = minimize(loss_and_grad, x0.ravel(), args=args, jac=True, method="SLSQP",
                       constraints=cons, options={"maxiter": maxiter, "ftol": 1e-12})
        X = res.x.reshape(n, 2)
        if not is_legal(X):
            # fallback: penalty method, then a final SLSQP polish from the legal point
            res = minimize(_penalised, x0.ravel(), args=args + (1e3,), jac=True, method="L-BFGS-B",
                           options={"maxiter": 2000})
            X = fit_device(res.x.reshape(n, 2))
            if is_legal(X):
                res2 = minimize(loss_and_grad, X.ravel(), args=args, jac=True, method="SLSQP",
                                constraints=cons, options={"maxiter": maxiter, "ftol": 1e-12})
                X2 = res2.x.reshape(n, 2)
                if is_legal(X2) and res2.fun < loss_and_grad(X.ravel(), *args)[0]:
                    X = X2
        dmin = float(np.linalg.norm(X[iu] - X[ju], axis=1).min())
        rad = float(np.linalg.norm(X, axis=1).max())
        diag.append((round(dmin, 3), round(rad, 2)))
        if is_legal(X):
            n_feas += 1
            val = loss_and_grad(X.ravel(), *args)[0]
            if val < best:
                best, best_x = val, X  # keep as optimised: pulser measures the radius from the origin
    if best_x is None:
        raise RuntimeError(f"no feasible layout found; per-restart (min dist, radius) = {diag}; "
                           f"r* range [{np.min(rstar[np.isfinite(rstar) & (rstar > 0)]):.2f}, {np.max(rstar[np.isfinite(rstar)]):.2f}]")
    return best_x, {"loss": float(best), "restarts": restarts, "feasible_restarts": n_feas}
