package user

import (
	"github.com/go-chi/chi"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	"github.com/go-playground/validator/v10"
	resp "kth_activities_helper/internal/lib/response"
	"kth_activities_helper/internal/models"
	"log/slog"
	"net/http"
	"strconv"
)

type EditRequest struct {
	DiscordId uint64 `json:"discord_id" validate:"required,gte=0"`
	Rating    uint32 `json:"rating" validate:"required,gte=0"`
	Username  string `json:"username" validate:"required"`
	Active    bool   `json:"active" validate:"required,bool"`
}

type EditResponse struct {
	resp.Response
	User models.User `json:"user,omitempty"`
}

type UserEditor interface {
	EditUser(osuId uint64, discordId uint64, rating uint32, username string, active bool) (models.User, error)
}

func EditUser(log *slog.Logger, userEditor UserEditor) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.user.edit.Edit"
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

		var req EditRequest

		err = render.DecodeJSON(r.Body, &req)
		if err != nil {
			localLog.Error("Failed to decode request body")
			render.JSON(w, r, resp.BadRequest("Failed to decode request"))
			return
		}

		if err := validator.New().Struct(req); err != nil {
			validateErr := err.(validator.ValidationErrors)
			localLog.Error("Failed to validate request")
			render.JSON(w, r, resp.ValidationError(validateErr))
			return
		}

		user, err := userEditor.EditUser(id, req.DiscordId, req.Rating, req.Username, req.Active)
		if err != nil {
			localLog.Error("Failed to edit user", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to edit user"))
		}

		// TODO delete
		localLog.Info("Edited user", slog.Uint64("osu_id", user.OsuId))

		render.JSON(w, r, EditResponse{
			Response: resp.OK(),
			User:     user,
		})
		return
	}
}
