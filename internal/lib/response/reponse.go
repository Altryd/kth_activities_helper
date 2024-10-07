package response

import (
	"fmt"
	"github.com/go-playground/validator/v10"
	"strings"
)

type Response struct {
	Status string `json:"status"`
	Error  string `json:"error,omitempty"`
}

const (
	StatusOK                  = "OK"
	StatusBadRequest          = "Bad Request"
	StatusUnauthorized        = "Unauthorized"
	StatusForbidden           = "Forbidden"
	StatusNotFound            = "Not Found"
	StatusInternalServerError = "Internal Server Error"
)

func OK() Response {
	return Response{
		Status: StatusOK,
	}
}

func BadRequest(msg string) Response {
	return Response{
		Status: StatusBadRequest,
		Error:  msg,
	}
}

func Error(msg string) Response {
	return Response{
		Status: StatusInternalServerError,
		Error:  msg,
	}
}

func ValidationError(errs validator.ValidationErrors) Response {
	var errMsgs []string
	for _, err := range errs {
		switch err.ActualTag() {
		case "required":
			errMsgs = append(errMsgs, fmt.Sprintf("Field %s is required", err.Field()))
		default:
			errMsgs = append(errMsgs, fmt.Sprintf("Field %s is not valid", err.Field()))
		}
	}

	return Response{
		Status: StatusBadRequest,
		Error:  strings.Join(errMsgs, "; "),
	}
}
