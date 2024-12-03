package security

import (
	"errors"
	"fmt"
	"github.com/dgrijalva/jwt-go"
	"kth_activities_helper/internal/config"
)

func ValidateToken(tokenString string, tokenType string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("invalid token signing method")
		}
		return []byte(config.AppConfig.SecurityConfig.SecretKey), nil
	})
	if err != nil {
		return nil, err
	}

	claims, ok := token.Claims.(*Claims)
	if !ok || !token.Valid {
		return nil, errors.New("invalid token")
	}

	/* if tokenType == "refresh" && claims.Subject != "refresh" {
		return nil, errors.New("invalid token")
	} */
	if tokenType == "refresh" && claims.Subject != "refresh" {
		return nil, errors.New("invalid token")
	}

	return claims, nil
}
