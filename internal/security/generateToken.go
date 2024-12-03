package security

import (
	"github.com/dgrijalva/jwt-go"
	"kth_activities_helper/internal/config"
	"kth_activities_helper/internal/models"
	"time"
)

type Claims struct {
	OsuUserID     uint64 `json:"osu_user_id"`
	DiscordUserId uint64 `json:"discord_user_id"`
	jwt.StandardClaims
}

func GenerateToken(user *models.User, tokenType string) (string, error) {
	var expirationTime int64
	var subject string

	if tokenType == "access" {
		expirationTime = time.Now().Add(time.Hour * 1).Unix() // expire in 1 hour
	} else if tokenType == "refresh" {
		expirationTime = time.Now().Add(time.Hour * 24 * 7).Unix() // expire in 7 days
		subject = "refresh"
	}

	claims := &Claims{
		OsuUserID:     user.OsuId,
		DiscordUserId: user.DiscordId,
		StandardClaims: jwt.StandardClaims{
			ExpiresAt: expirationTime,
			Issuer:    "myapp",
			Subject:   subject,
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)

	accessToken, err := token.SignedString([]byte(config.AppConfig.SecurityConfig.SecretKey))

	if err != nil {
		return "", err
	}

	return accessToken, nil
}
