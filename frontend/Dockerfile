FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

#  Serve the 'build' directory
CMD ["npm", "run", "dev"]