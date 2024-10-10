package user

import (
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	"github.com/go-playground/validator/v10"
	resp "kth_activities_helper/internal/lib/response"
	"log/slog"
	"net/http"
)

type Request struct {
	OsuId     uint64 `json:"osu_id" validate:"required,gte=0"`
	DiscordId uint64 `json:"discord_id" validate:"required,gte=0"`
	Rating    uint32 `json:"rating" validate:"required,gte=0"`
	Username  string `json:"username" validate:"required"`
	Active    bool   `json:"active" validate:"required,bool"`
}

type CreateResponse struct {
	resp.Response
	OsuId uint64 `json:"osu_id,omitempty"`
}

type UserCreator interface {
	CreateUser(osuId uint64, discordId uint64, rating uint32, username string, active bool) (uint64, error)
}

func New(log *slog.Logger, userCreator UserCreator) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.user.create.New"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		var req Request

		err := render.DecodeJSON(r.Body, &req)
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

		id, err := userCreator.CreateUser(req.OsuId, req.DiscordId, req.Rating, req.Username, req.Active)
		if err != nil {
			localLog.Error("Failed to create user", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to create match"))
		}

		// TODO delete
		localLog.Info("Created user", slog.Uint64("osu_id", id))

		render.JSON(w, r, CreateResponse{
			Response: resp.OK(),
			OsuId:    id,
		})
		return
	}
}
