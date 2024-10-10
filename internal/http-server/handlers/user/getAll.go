package user

import (
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/models"
	"log/slog"
	"net/http"
)

type GetAllResponse struct {
	resp.Response
	Users []models.User `json:"matches,omitempty"`
}

type UsersSelector interface {
	SelectUsers() ([]models.User, error)
}

func GetAll(log *slog.Logger, usersSelector UsersSelector) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.user.get.GetAll"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		users, err := usersSelector.SelectUsers()
		if err != nil {
			localLog.Error("Failed to select all users", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to select all users"))
		}

		localLog.Info("Selected all users")

		render.JSON(w, r, GetAllResponse{
			Response: resp.OK(),
			Users:    users,
		})
		return
	}
}
