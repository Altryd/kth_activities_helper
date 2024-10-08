package matchType

import (
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	"github.com/go-playground/validator/v10"
	resp "kth_activities_helper/internal/lib/response"
	"log/slog"
	"net/http"
)

type Request struct {
	Name string `json:"name" validate:"required,min=3,max=40"`
}

type Response struct {
	resp.Response
	MatchTypeId uint64 `json:"match_id,omitempty"`
}

type MatchTypeCreator interface {
	CreateMatchType(matchTypeName string) (uint64, error)
}

func New(log *slog.Logger, matchTypeCreator MatchTypeCreator) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.matchType.create.New"
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

		id, err := matchTypeCreator.CreateMatchType(req.Name)
		if err != nil {
			localLog.Error("Failed to create match type", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error("Failed to create match type"))
		}

		// TODO delete
		localLog.Info("Created match type", slog.Uint64("match_type_id", id))

		render.JSON(w, r, Response{
			Response:    resp.OK(),
			MatchTypeId: id,
		})

		render.JSON(w, r, resp.OK())
		return
	}
}
