package match

import (
	"fmt"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/render"
	resp "kth_activities_helper/internal/lib/response"
	"log/slog"
	"net/http"
	"strconv"
)

/*
type EditRequest struct {
	TypeId     uint64    `json:"type_id" validate:"required,gte=0"`
	Date       time.Time `json:"date" validate:"required,datetime"`
	IsApproved bool      `json:"is_approved" validate:"required,bool"`
} */

type DeleteResponse struct {
	resp.Response
	Success bool `json:"success,omitempty"`
}

type MatchDeletor interface {
	DeleteMatch(matchId uint64) (bool, error)
}

func Delete(log *slog.Logger, matchDeletor MatchDeletor) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		const op = "handlers.match.delete.Delete"
		localLog := log.With(
			slog.String("op", op),
			slog.String("request_id", middleware.GetReqID(r.Context())),
		)

		marchId := chi.URLParam(r, "id")
		id, err := strconv.ParseUint(marchId, 10, 64)
		if err != nil {
			http.Error(w, http.StatusText(400), 400)
			return
		}
		/*
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
		*/
		_, err = matchDeletor.DeleteMatch(id)
		if err != nil {
			localLog.Error("Failed to delete match", slog.String("error", err.Error()))
			render.JSON(w, r, resp.Error(fmt.Sprintf("Failed to delete match, %s", err)))
			return
		}

		// TODO delete
		localLog.Info("Deleted match", slog.Uint64("match_id", id))

		render.JSON(w, r, DeleteResponse{
			Response: resp.OK(),
			Success:  true,
		})
		return
	}
}
