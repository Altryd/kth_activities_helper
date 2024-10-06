package models

type User struct {
	OsuId          uint64           `gorm:"primary_key;autoIncrement:false" json:"osu_id"`
	DiscordId      uint64           `json:"discord_id"`
	Rating         uint32           `json:"rating"`
	Username       string           `json:"username"`
	Active         bool             `gorm:"default:false" json:"active"`
	MatchUserScrim []MatchUserScrim `gorm:"foreignKey:PlayerId;references:OsuId"`
}
