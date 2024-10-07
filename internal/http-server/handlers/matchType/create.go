package match

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
	CreateMatchType(matchTypeName string)
}

func New(log *slog.Logger) http.HandlerFunc {
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

		// TODO Создать запись в бд и обработать ошибку

		render.JSON(w, r, resp.OK())
		return
	}
}
