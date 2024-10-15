package user

import (
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/models"
	"log/slog"
	"net/http"
	"strconv"
)

// TODO добавить дополнительную статистику по изменению рейтинга пользователя

type GetOneResponse struct {
	resp.Response
	User models.User `json:"user,omitempty"`
}

type OneUserSelector interface {
	SelectOneUser(osuId uint64) (models.User, error)
}

func GetOne(log *slog.Logger, oneUserSelector OneUserSelector) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.user.get.GetOne"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)
		osuId := chi.URLParam(r, "osuId")
		id, err := strconv.ParseUint(osuId, 10, 64)
		if err != nil {
			http.Error(w, http.StatusText(400), 400)
			return
		}

		user, err := oneUserSelector.SelectOneUser(id)
		if err != nil {
			localLog.Error("Failed to select user", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to select user"))
		}

		localLog.Info("Selected user", slog.Uint64("user_id", user.OsuId))

		render.JSON(w, r, GetOneResponse{
			Response: resp.OK(),
			User:     user,
		})
		return
	}
}
