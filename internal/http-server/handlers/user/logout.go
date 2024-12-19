package user

import (
	"github.com/go-chi/chi/v5/middleware"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/security"
	"log/slog"
	"net/http"
)

type LogoutResponse struct {
	resp.Response
}

func Logout(log *slog.Logger) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.user.get.Logout"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		security.SetCookie(w, "jwt-kth", "", -1)
		http.Redirect(w, r, "http://localhost:3000/users", 302)
		localLog.Info("Successful logout")
		return
	}
}
