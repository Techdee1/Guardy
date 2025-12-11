# Twilio SMS Setup for FloodGuard Nigeria

To enable SMS notifications to emergency centers, you need to configure Twilio credentials.

## Steps to Configure Twilio

1. **Create a Twilio Account**
   - Go to [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
   - Sign up for a free trial account

2. **Get Your Credentials**
   - After logging in, go to your [Twilio Console Dashboard](https://console.twilio.com/)
   - You'll find your **Account SID** and **Auth Token**

3. **Get a Phone Number**
   - In the Twilio Console, go to "Phone Numbers" > "Manage" > "Buy a number"
   - Purchase a phone number (trial accounts get one free number)
   - Note your Twilio phone number (format: +1234567890)

4. **Configure Environment Variables**

   The Supabase Edge Function needs these three environment variables:

   - `TWILIO_ACCOUNT_SID` - Your Twilio Account SID
   - `TWILIO_AUTH_TOKEN` - Your Twilio Auth Token
   - `TWILIO_PHONE_NUMBER` - Your Twilio phone number (with country code)

   These are automatically configured in your Supabase project.

5. **Test SMS Notifications**
   - Submit an emergency report through the application
   - Emergency centers within 10km will receive SMS notifications
   - Check your Twilio Console logs to verify SMS delivery

## Trial Account Limitations

- Twilio trial accounts can only send SMS to verified phone numbers
- To verify a number: Twilio Console > Phone Numbers > Manage > Verified Caller IDs
- Upgrade to a paid account to send to any number

## Costs

- SMS pricing varies by country
- Nigeria SMS: ~$0.035 per message
- Check current pricing: [https://www.twilio.com/sms/pricing](https://www.twilio.com/sms/pricing)

## Troubleshooting

If SMS is not working:
- Check that all environment variables are set correctly
- Verify your Twilio account is active
- Check the phone number format includes country code (+234 for Nigeria)
- Review Twilio Console logs for error messages
- Ensure you have sufficient account balance (for paid accounts)
