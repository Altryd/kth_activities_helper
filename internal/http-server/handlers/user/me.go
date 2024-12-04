package user

import (
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/security"
	"log/slog"
	"net/http"
)

func GetMe(log *slog.Logger, oneUserSelector OneUserSelector) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.user.get.GetOne"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)
		jwt_token, err := r.Cookie("jwt-kth")
		//fmt.Println("cookie auth middleware: ", jwt_token, err)
		//fmt.Println("cookies: ", r.Cookies())
		// jwt_token, err := c.Cookie("jwt")
		if err != nil {
			w.WriteHeader(http.StatusUnauthorized)
			// c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
			return
		}

		claims, err := security.ValidateToken(jwt_token.Value, "access")

		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			return
			// c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		}

		/*
			osuId := chi.URLParam(r, "osuId")
			id, err := strconv.ParseUint(osuId, 10, 64)
			if err != nil {
				http.Error(w, http.StatusText(400), 400)
				return
			} */

		user, err := oneUserSelector.SelectOneUser(claims.OsuUserID)
		if err != nil {
			localLog.Error("Failed to select user", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to select user"))
			return
		}

		localLog.Info("Selected user", slog.Uint64("user_id", user.OsuId))

		render.JSON(w, r, GetOneResponse{
			Response: resp.OK(),
			User:     user,
		})
		return
	}
}
